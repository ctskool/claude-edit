"""Lay skin screenshots out on one labelled sheet.
Run: python tools/beat_review_v2/skin_sheet.py <out.png> <skin> [<skin> ...]
Reads reports/player-skins/<skin>.png (1600x900), writes a 3-across grid of half-size tiles."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

SHOTS = Path(__file__).resolve().parents[2] / 'reports' / 'player-skins'
TILE, LABEL, GAP = (800, 450), 34, 16


def main(out, names):
    cols = min(3, len(names))
    rows = -(-len(names) // cols)
    w = cols * TILE[0] + (cols + 1) * GAP
    h = rows * (TILE[1] + LABEL) + (rows + 1) * GAP
    sheet = Image.new('RGB', (w, h), (24, 24, 24))
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype('consola.ttf', 22)
    except OSError:
        font = ImageFont.load_default()
    for i, name in enumerate(names):
        x = GAP + (i % cols) * (TILE[0] + GAP)
        y = GAP + (i // cols) * (TILE[1] + LABEL + GAP)
        draw.text((x, y + 4), name, fill=(235, 235, 235), font=font)
        shot = Image.open(SHOTS / f'{name}.png').convert('RGB').resize(TILE, Image.LANCZOS)
        sheet.paste(shot, (x, y + LABEL))
    sheet.save(out)
    print(out)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2:])
