"""Word-level transcript for a video/audio file using faster-whisper.

Usage: python transcribe.py <media> <out.json> [model] [glossary prompt] [language|auto]
Writes {"text", "segments":[{start,end,text,words:[{start,end,word}]}]}.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_whisper as load_model  # noqa: E402  (CUDA fp16 on NVIDIA, CPU int8 elsewhere)


def main():
    media, out = sys.argv[1], sys.argv[2]
    model_name = sys.argv[3] if len(sys.argv) > 3 else "large-v3"
    glossary = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] else None
    language = sys.argv[5] if len(sys.argv) > 5 else "en"
    model = load_model(model_name)
    segments, info = model.transcribe(media, word_timestamps=True, vad_filter=True,
                                      language=None if language == "auto" else language, initial_prompt=glossary)
    data = {"language": info.language, "duration": info.duration, "segments": []}
    for s in segments:
        data["segments"].append({
            "start": round(s.start, 3),
            "end": round(s.end, 3),
            "text": s.text.strip(),
            "words": [{"start": round(w.start, 3), "end": round(w.end, 3), "word": w.word.strip()} for w in (s.words or [])],
        })
    data["text"] = " ".join(s["text"] for s in data["segments"])
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print(data["text"])


if __name__ == "__main__":
    main()
