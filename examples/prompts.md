# Prompt examples

Type these in Claude Code, opened in this repo's folder. Paths can be absolute or relative; quote paths with spaces.

## First run

```text
/claude-edit-setup                       check the install, then answer the brand questions
redo my setup                            change your brand, colours or fonts later
```

## Make edits

```text
/claude-edit my-video.mp4                                 ivory (the default style)
/claude-edit my-video.mp4 ivory and rotation              two versions to A/B test
/claude-edit my-video.mp4 ivory + all formats             ivory, rotation, frost and popout
/claude-edit "~/Movies/2026-10-27 20-25-26.mkv"           raw OBS take: tight-cut first, then ivory
/claude-edit take1.mkv take2.mkv frost                    two raw takes of one short, frost format
/claude-edit-cut take1.mkv take2.mkv                      just the verified tight cut, no graphics
/claude-edit-popout my-video.mp4                          one format only (any /claude-edit-<menu name>)
/claude-edit-versus take.mkv                              Raw vs Claude from one 16:9 take
```

Helpful extras in the same message:

```text
/claude-edit my-video.mp4 rotation - it's about https://github.com/owner/repo, screenshot the README
/claude-edit my-video.mp4 ivory - the product is spelled "Kimi K3.1 Pro", Whisper keeps writing "Kimmy"
/claude-edit my-export.mp4 - it's a finished export with burned-in captions in the face half
```

## Follow-ups

```text
polish the rotation version                               one more critic + fix round, then re-render
the captions cover my mouth at 0:12 in frost              targeted fix
send me the phone previews                                the < 30 MB copies in out/preview/
make a gallery page of every version of this video        out/<id>-formats.html
render the final of frost                                 draft -> final quality
```

## Raw vs Claude: what to say on camera

> These two videos are exactly the same, except one was edited by Claude. And you can watch those edits happen in real
> time. First, give me captions. Now make the key words pop. Now let's change the colouring, make it a bit warmer.
> Next, put a big title behind my head that says "no editor needed". Now add a panel that shows everything we've edited
> so far, update it as we go, and add a small sound when it changes something. Pull the camera a little closer to me.
> Now pull it back to where it originally was. Bring in some music, but make it a little bit quieter so you can still
> hear me. Now try softening the background even more. And for the last bit, make the captions a completely different
> font. So with that, you can see how powerful video editing is with Claude.

Anything outside the built-in edits (say "flip it to black and white" or "add a lower third with my name") becomes
an edit too. Claude maps it to the closest built-in op or writes a custom one.
