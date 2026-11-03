# Ivory lock test

Status: not locked. No version is named or frozen, and no run counts yet.
A lock means "this exact version gave acceptable first renders within this scope". It is not a promise. [Ours]

## What is under test

- **One named ivory version and one spine version, frozen before raw 1.** [Chase] [Ours]
  Why: a lock has to mean one exact version passed. Met when: both versions are in the record below.
- **Nothing that changes the output moves during the streak.** Sizes, colours, levels and the transcription engine included. [Ours]
  Taste changes wait in a queue. Logs or a review page can change, since they do not touch the output.
  Why: a moving version proves nothing. Met when: adopting a queued change starts a new version and a new streak.
- **Scope:** Chase solo, 9:16, 2160x3840 OBS source, the chosen rig, tool-news or how-to. Any length: a video runs as long as it runs, up to about 3 minutes and beyond. [Chase]

## The raws

Three new ones, all filmed after the build. None exists now. [Chase] [Ours]
1. A hard one first, as Chase rates it: tool demo, heavy on sources and screens.
2. News or opinion with no product. Check his next 10 planned shorts first, and swap this kind if it is not real for him.
3. A restart-heavy how-to.

A repeat of a kind already passed does not count toward three, and a defect on it still resets. [Ours]

## Each run [Ours]

1. The spine runs. Chase does the one-minute phone listen.
2. Ivory runs to first render with no human touch and no Claude fixes. Save that file and record its fingerprint.
3. Checks run on that file. Prepare the machine defect list. Repair nothing yet.
4. Chase watches and listens to the untouched render, defect list beside it. Each note is tagged defect or taste. He has final say.
5. He answers one question: would you publish this first render, apart from optional tweaks?
6. After that verdict, repairs can happen. He approves and gets one CapCut draft. Repairs finish the video but cannot rescue the attempt.
7. The attempt stays pending until hand work is logged, with whether he opened and finished the draft there.

## A run counts only if all of these hold [Ours]

- Every required check is green on the first render, with no waivers and no UNVERIFIED.
- Zero cut notes.
- Zero defect notes, including hand fixes he classes as defects.
- Publishable is yes.
- Hand status is closed.

## What resets the streak [Ours]

| Event | Effect |
|---|---|
| Failed, waived or unverified required check | Resets |
| Cut note | Resets. The spine and ivory qualify together |
| Defect note | Resets |
| Publishable is no | Resets, even if every note was taste |
| Any adopted change that affects output | New version, streak restarts at zero |
| Taste note, not adopted | Never resets |

## On a lock [Ours]

- Record the raws, exact versions, date and scope here.
- The spine stop goes away.
- Changing a locked value needs Chase's yes plus a smoke run.
- A later defect reopens the lock. A new device on a locked template gets named in the report and does not unlock it.

**Stop rule:** if six raws pass without a lock, stop and review the ledger. [Ours]

Per run, `runs.jsonl` also logs: check verdicts, note counts by class, the publishable answer, hand status and summary, review minutes, repair rounds, processing time, Mtok, usage before and after, and CapCut version. [Ours]

## Record

Ivory version: not named. Spine version: not named. Streak: 0 of 3. Locked on: not locked.

| Raw | Kind | Date | First render file and fingerprint | Required checks | Cut notes | Defect notes | Publishable | Hand status | Counts |
|---|---|---|---|---|---|---|---|---|---|
| | | | | | | | | | |
