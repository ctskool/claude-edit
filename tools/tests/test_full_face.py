"""Full-face gate for /claude-edit: motionlint, both workflows, the template rule files.

Usage: python tools/tests/test_full_face.py
The workflows run in node with agent, parallel, pipeline, phase, log and args stubbed, and their prompts are captured.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MOTIONLINT = os.path.join(ROOT, "tools", "motionlint.py")
WORKFLOWS = os.path.join(ROOT, "tools", "workflows", "next")
TEMPLATES = os.path.join(ROOT, "templates")
FACE_HTML = '<!doctype html><video id="f" src="assets/face_full.mp4"></video>\n'
PLAIN_HTML = '<!doctype html><video id="f" src="assets/face_half.mp4"></video>\n'
HIS_WORDS = 'do a "full screen" edit on the CTA'

# A workflow script is a module body with a top-level return, so it runs as an async function here.
HARNESS = r"""
import { readFileSync } from 'node:fs'
const [script, argsJson, planCheckJson, repliesJson] = process.argv.slice(2)
const replies = JSON.parse(repliesJson)
const code = readFileSync(script, 'utf8').replace(/^export const meta/m, 'const meta')
const prompts = []
const reply = (label) => {
  if (Object.hasOwn(replies, label)) return replies[label]
  if (label === 'research') return { topic: 't', facts: {}, capture: [], source_story: [], unverifiable: [] }
  if (label === 'check') return { ok: false, issues: [{ beat: 'b01', problem: 'stub plan problem', fix: 'stub fix' }] }
  if (label.startsWith('plancheck')) return JSON.parse(planCheckJson)
  if (label.startsWith('build')) return { lint_errors: 0, motionlint: 'ok', snaps_dir: 's', self_review: 'r' }
  return { files: [], notes: '' }
}
const agent = async (prompt, opts) => { prompts.push({ label: opts.label, prompt, schema: opts.schema }); return reply(opts.label) }
const parallel = (thunks) => Promise.all(thunks.map((t) => t()))
const pipeline = (items, ...stages) => Promise.all(items.map(async (item) => {
  let r = item
  for (const stage of stages) r = await stage(r, item)
  return r
}))
const AsyncFunction = (async () => {}).constructor
const run = new AsyncFunction('agent', 'parallel', 'pipeline', 'phase', 'log', 'args', code)
const result = await run(agent, parallel, pipeline, () => {}, () => {}, {root: '/stub/root', ...JSON.parse(argsJson)})  // the skill always passes root
console.log(JSON.stringify({ result, prompts }))
"""


def lint(plan_text, html=FACE_HTML, pack="editorial", relative=False):
    """Run motionlint on a temp project. plan_text None means no plan.json."""
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
            f.write(html)
        if plan_text is not None:
            with open(os.path.join(d, "plan.json"), "w", encoding="utf-8") as f:
                f.write(plan_text)
        cmd = [sys.executable, MOTIONLINT, "index.html" if relative else os.path.join(d, "index.html")]
        if pack:
            cmd += ["--pack", pack]
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=d if relative else ROOT)
    return r.returncode, r.stdout


class Motionlint(unittest.TestCase):
    def blocked(self, plan_text):
        code, out = lint(plan_text)
        self.assertEqual(code, 2, out)
        self.assertIn("ERROR face_full", out)
        self.assertIn("off unless a template or Chase turns it on", out)

    def test_no_plan_json_fails(self):
        self.blocked(None)

    def test_no_field_fails(self):
        self.blocked('{"beats": []}')

    def test_string_true_fails(self):
        self.blocked('{"allow_full_face": "true"}')

    def test_other_non_boolean_values_fail(self):
        for value in ('1', 'null', '"yes"', '[true]', '{"on": true}'):
            with self.subTest(value=value):
                self.blocked('{"allow_full_face": %s}' % value)

    def test_boolean_false_fails(self):
        self.blocked('{"allow_full_face": false}')

    def test_unusable_plan_json_fails(self):
        for text in ('{not json', '', '[true]', 'true'):
            with self.subTest(text=text):
                self.blocked(text)

    def test_boolean_true_passes(self):
        code, out = lint('{"allow_full_face": true, "allow_full_face_source": "template"}')
        self.assertEqual(code, 0, out)
        self.assertNotIn("face_full", out)

    def test_boolean_true_passes_on_a_relative_path(self):
        # recut-build.js runs motionlint on index.html from inside the project.
        code, out = lint('{"allow_full_face": true}', relative=True)
        self.assertEqual(code, 0, out)

    def test_no_face_full_passes(self):
        for plan_text in (None, '{"allow_full_face": false}', '{"allow_full_face": "true"}'):
            with self.subTest(plan_text=plan_text):
                code, out = lint(plan_text, html=PLAIN_HTML)
                self.assertEqual(code, 0, out)

    def test_other_packs_stay_as_they_were(self):
        code, out = lint(None, pack=None)
        self.assertEqual(code, 0, out)


PLAN_PASSES = {"ok": True, "issues": []}


def run_workflow(script, args, plan_check=PLAN_PASSES, replies=None):
    """Run one workflow with stubs. Returns its result and prompts."""
    with tempfile.TemporaryDirectory() as d:
        harness = os.path.join(d, "harness.mjs")
        with open(harness, "w", encoding="utf-8") as f:
            f.write(HARNESS)
        r = subprocess.run(["node", harness, os.path.join(WORKFLOWS, script), json.dumps(args), json.dumps(plan_check), json.dumps(replies or {})],
                           capture_output=True, text=True, encoding="utf-8", cwd=d)
    if r.returncode:
        raise AssertionError(f"{script} failed in node:\n{r.stderr}")
    return json.loads(r.stdout)


def dry_run(script, args, plan_check=PLAN_PASSES):
    """Run one workflow with stubs. Returns {label: prompt}."""
    return {p["label"]: p["prompt"] for p in run_workflow(script, args, plan_check)["prompts"]}


PLAN_ARGS = {"id": "t1", "source": "cut.mp4", "hints": [], "jumpcuts": [12.5]}
BUILD_ARGS = {"id": "t1", "styles": ["editorial"], "ref": "1022-2"}
OFF = {"allowFullFace": False, "allowFullFaceSource": "template"}
ON_TEMPLATE = {"allowFullFace": True, "allowFullFaceSource": "template"}
ON_WORDS = {"allowFullFace": True, "allowFullFaceSource": HIS_WORDS}
PUNCH_MARK = "covers jump cut at <t> with a bottom-half punch-in"


class Workflows(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan_off = dry_run("recut-plan.js", {**PLAN_ARGS, **OFF})
        cls.plan_on = dry_run("recut-plan.js", {**PLAN_ARGS, **ON_WORDS})
        cls.build_off = dry_run("recut-build.js", {**BUILD_ARGS, **OFF})
        cls.build_on = dry_run("recut-build.js", {**BUILD_ARGS, **ON_WORDS})

    def test_every_stage_ran(self):
        self.assertEqual(list(self.plan_off), ["research", "assets", "plan", "check", "plan-revise"])
        self.assertEqual(list(self.plan_on), ["research", "assets", "plan", "check", "plan-revise"])
        self.assertEqual(list(self.build_off), ["direct:editorial", "plancheck:editorial", "build:editorial"])
        self.assertEqual(list(self.build_on), ["direct:editorial", "plancheck:editorial", "build:editorial"])

    def test_default_and_non_boolean_are_off(self):
        for args in ({}, {"allowFullFace": "true"}, {"allowFullFace": 1}):
            with self.subTest(args=args):
                self.assertEqual(dry_run("recut-plan.js", {**PLAN_ARGS, **args}), self.plan_off)
                self.assertEqual(dry_run("recut-build.js", {**BUILD_ARGS, **args}), self.build_off)

    def test_no_args_at_all_is_off(self):
        self.assertIn("allow_full_face false", dry_run("recut-build.js", None)["direct:editorial"])

    def test_template_opt_in_is_on(self):
        p = dry_run("recut-plan.js", {**PLAN_ARGS, **ON_TEMPLATE})["plan"]
        self.assertIn("allow_full_face to true (a JSON Boolean) and allow_full_face_source to \"template\"", p)
        self.assertIn("'face' (his opinion or emphasis", p)

    def test_every_agent_gets_the_setting(self):
        for prompts in (self.plan_off, self.build_off):
            for label, p in prompts.items():
                self.assertIn("This run has allow_full_face false", p, label)
        for prompts in (self.plan_on, self.build_on):
            for label, p in prompts.items():
                self.assertIn("This run has allow_full_face true", p, label)

    def test_planner_off_excludes_full_face(self):
        p = self.plan_off["plan"]
        self.assertIn("NEVER 'face': a full-screen face is off for this run", p)
        self.assertIn("on a quiet top panel with one big serif line", p)
        self.assertNotIn("'face' (his opinion", p)
        self.assertNotIn("assets/face_full.mp4", p)
        self.assertIn("allow_full_face to false (a JSON Boolean)", p)
        self.assertIn("allow_full_face, allow_full_face_source, beats[]", p)

    def test_planner_on_offers_full_face(self):
        p = self.plan_on["plan"]
        self.assertIn("'face' (his opinion or emphasis", p)
        self.assertIn("assets/face_full.mp4", p)
        self.assertNotIn("NEVER 'face'", p)
        self.assertIn("allow_full_face to true (a JSON Boolean)", p)
        self.assertIn(json.dumps(HIS_WORDS), p)

    def test_jump_cuts_follow_the_setting(self):
        self.assertIn("quick punch-in inside the bottom half only (scale about 1.08)", self.plan_off["plan"])
        self.assertNotIn("a beat with layout_hint 'face'", self.plan_off["plan"])
        self.assertIn("a beat with layout_hint 'face' (a full-face punch-in) or 'takeover' must START", self.plan_on["plan"])
        self.assertNotIn("punch-in inside the bottom half", self.plan_on["plan"])

    def test_jump_covers_reach_the_plan_check(self):
        self.assertIn("Every jump cut in [12.5] has a cover: a beat with layout_hint 'takeover'", self.plan_off["check"])
        self.assertIn("Every jump cut in [12.5] has a cover: a beat with layout_hint 'face'", self.plan_on["check"])

    def test_no_jump_cut_list_means_no_check_item(self):
        args = {k: v for k, v in PLAN_ARGS.items() if k != "jumpcuts"}
        self.assertNotIn("has a cover", dry_run("recut-plan.js", {**args, **OFF})["check"])

    def test_bottom_half_punch_in_reaches_the_build(self):
        self.assertIn(PUNCH_MARK, self.plan_off["plan"])
        self.assertNotIn(PUNCH_MARK, self.plan_on["plan"])
        for label in ("direct:editorial", "build:editorial"):
            self.assertIn(PUNCH_MARK, self.build_off[label], label)
            self.assertIn("punch-in on face_half.mp4", self.build_off[label], label)
            self.assertNotIn(PUNCH_MARK, self.build_on[label], label)
        self.assertIn("punch-in jump cover with no punch-in in plan.json is a defect", self.build_off["plancheck:editorial"])
        self.assertNotIn("punch-in jump cover", self.build_on["plancheck:editorial"])

    def test_emphasis_list_follows_the_setting(self):
        self.assertNotIn("face/takeover", self.plan_off["plan"])
        self.assertIn("strongest quiet-panel/takeover beats", self.plan_off["plan"])
        self.assertIn("strongest face/takeover beats", self.plan_on["plan"])

    def test_plan_check_treats_full_face_as_a_defect_only_when_off(self):
        self.assertIn("is a full-face beat and a defect", self.plan_off["check"])
        self.assertNotIn("'split', 'takeover' or 'face'", self.plan_off["check"])
        self.assertIn("'split', 'takeover' or 'face'", self.plan_on["check"])
        self.assertNotIn("is a full-face beat and a defect", self.plan_on["check"])

    def test_plan_check_issues_still_flow(self):
        self.assertIn("stub plan problem", self.plan_off["plan-revise"])
        self.assertIn("stub plan problem", self.plan_on["plan-revise"])

    def test_build_refuses_a_plan_check_that_did_not_pass(self):
        failed = {"ok": False, "issues": ["stub plan-check issue"]}
        for check in (failed, None, {}, {"ok": "true", "issues": []}, {"ok": True}, {"ok": True, "issues": ["left over"]}):
            with self.subTest(check=check):
                run = run_workflow("recut-build.js", BUILD_ARGS, check)
                self.assertEqual([p["label"] for p in run["prompts"]], ["direct:editorial", "plancheck:editorial"])
                self.assertEqual(len(run["result"]), 1)
                self.assertIs(run["result"][0]["refused"], True)
                self.assertNotIn("build", run["result"][0])

    def test_build_runs_on_a_passed_plan_check(self):
        run = run_workflow("recut-build.js", BUILD_ARGS)
        self.assertIs(run["result"][0]["refused"], False)
        self.assertEqual(run["result"][0]["build"]["motionlint"], "ok")

    def test_builder_never_sees_plan_check_issues(self):
        self.assertNotIn("Plan-check issues", self.build_off["build:editorial"])
        self.assertNotIn("Plan-check issues", self.build_on["build:editorial"])

    def test_build_off_never_uses_face_full(self):
        for label in ("direct:editorial", "build:editorial"):
            p = self.build_off[label]
            self.assertIn("NEVER use face_full.mp4", p, label)
            self.assertIn("SPLIT SCREEN in every style", p, label)
        self.assertIn("the layout (split / full-graphic), the component", self.build_off["direct:editorial"])
        self.assertIn("Leave face_full.mp4 out.", self.build_off["build:editorial"])
        self.assertIn("A full-face beat or any use of face_full.mp4 is a defect.", self.build_off["plancheck:editorial"])

    def test_build_on_allows_face_full(self):
        for label in ("direct:editorial", "build:editorial"):
            p = self.build_on[label]
            self.assertNotIn("NEVER use face_full.mp4", p, label)
            self.assertNotIn("SPLIT SCREEN in every style", p, label)
            self.assertIn("face_full.mp4 (full-frame face", p, label)
        self.assertIn("the layout (split / full-graphic / full-face), the component", self.build_on["direct:editorial"])
        self.assertNotIn("Leave face_full.mp4 out.", self.build_on["build:editorial"])
        self.assertIn("Full-face beats are allowed", self.build_on["plancheck:editorial"])
        self.assertNotIn("is a defect.", self.build_on["plancheck:editorial"].split("Defects only")[0].split("must both set")[1])

    def test_plan_json_carries_both_fields(self):
        self.assertIn('In plan.json set allow_full_face to false (a JSON Boolean) and allow_full_face_source to "template"', self.build_off["direct:editorial"])
        self.assertIn("In plan.json set allow_full_face to true (a JSON Boolean) and allow_full_face_source to " + json.dumps(HIS_WORDS), self.build_on["direct:editorial"])


class PlanCheckAndCodex(unittest.TestCase):
    """Warnings never block the build, and Codex is opt-in: the default run is plain Claude Code."""

    def test_warnings_alone_still_build_and_reach_the_builder(self):
        run = run_workflow("recut-build.js", BUILD_ARGS, {"ok": True, "issues": [], "warnings": ["outline 6 px left of b14's target"]})
        self.assertIs(run["result"][0]["refused"], False)
        build = {p["label"]: p["prompt"] for p in run["prompts"]}["build:editorial"]
        self.assertIn("Plan-check warnings, not blockers", build)
        self.assertIn("outline 6 px left of b14's target", build)

    def test_a_blocker_still_refuses_with_warnings_beside_it(self):
        run = run_workflow("recut-build.js", BUILD_ARGS, {"ok": False, "issues": ["b07 shows 40% but facts.json says 38%"], "warnings": ["easing"]})
        self.assertIs(run["result"][0]["refused"], True)

    def test_check_sorts_blockers_from_warnings(self):
        p = dry_run("recut-build.js", BUILD_ARGS)["plancheck:editorial"]
        self.assertIn("issues are blockers only", p)
        self.assertIn("geometry.py measures those on the built page", p)
        self.assertIn("When unsure which list, warn.", p)

    def test_default_run_has_no_codex(self):
        for args in ({}, {"codex": "true"}, {"codex": 1}):
            with self.subTest(args=args):
                plan = dry_run("recut-plan.js", {**PLAN_ARGS, **args})["plan"]
                direct = dry_run("recut-build.js", {**BUILD_ARGS, **args})["direct:editorial"]
                self.assertIn("never pick scene", plan)
                self.assertNotIn("may get a scene block", plan)
                self.assertIn("plan no scene images", direct)
                self.assertNotIn("codex exec", direct)

    def test_codex_true_keeps_scenes(self):
        plan = dry_run("recut-plan.js", {**PLAN_ARGS, "codex": True})["plan"]
        direct = dry_run("recut-build.js", {**BUILD_ARGS, "codex": True})["direct:editorial"]
        self.assertIn("may get a scene block", plan)
        self.assertIn("hand it to codex exec", direct)

    def test_research_stage_runs_alone_on_the_cut_words(self):
        run = run_workflow("recut-plan.js", {**PLAN_ARGS, "stage": "research", "words": "raw/cut_words.json"})
        self.assertEqual([p["label"] for p in run["prompts"]], ["research", "assets"])
        self.assertEqual(run["result"]["stage"], "research")
        self.assertIn("Transcript with word timings: raw/cut_words.json", run["prompts"][0]["prompt"])

    def test_beats_stage_skips_research_and_assets(self):
        labels = [p["label"] for p in run_workflow("recut-plan.js", {**PLAN_ARGS, "stage": "beats"})["prompts"]]
        self.assertEqual(labels, ["plan", "check", "plan-revise"])

    def test_unknown_stage_runs_everything(self):
        labels = [p["label"] for p in run_workflow("recut-plan.js", {**PLAN_ARGS, "stage": "nope"})["prompts"]]
        self.assertEqual(labels, ["research", "assets", "plan", "check", "plan-revise"])

    def test_skill_caps_plan_check_rounds_and_makes_codex_optional(self):
        p = read(ROOT, ".claude", "skills", "claude-edit", "SKILL.md")
        self.assertIn("**Two plan-check rounds at most:**", p)
        self.assertIn("Run `codex --version` once.", p)
        self.assertEqual(p.count("allowFullFaceSource, codex"), 4)


def read(*parts):
    with open(os.path.join(*parts), encoding="utf-8") as f:
        return f.read()


class Rules(unittest.TestCase):
    def test_ivory_is_off(self):
        with open(os.path.join(TEMPLATES, "ivory", "template.json"), encoding="utf-8") as f:
            t = json.load(f)
        self.assertEqual(t["name"], "ivory")
        self.assertEqual(t["tool_name"], "editorial")
        self.assertIs(t["full_face"], False)

    def test_every_template_carries_the_setting(self):
        names = [n for n in os.listdir(TEMPLATES) if os.path.isfile(os.path.join(TEMPLATES, n, "TEMPLATE.md"))]
        self.assertIn("ivory", names)
        for name in names:
            with self.subTest(template=name):
                with open(os.path.join(TEMPLATES, name, "template.json"), encoding="utf-8") as f:
                    self.assertIsInstance(json.load(f)["full_face"], bool)

    def test_layout_comes_first_follows_the_setting(self):
        p = read(TEMPLATES, "ivory", "picker.md")
        self.assertIn("With `full_face` on, a full-face trigger in `layout.md` takes `face`.", p)
        self.assertIn("With it off, an opinion, payoff or CTA line takes `face`.", p)

    def test_join_spacing_spares_joins_inside_a_takeover(self):
        p = read(TEMPLATES, "ivory", "layout.md")
        self.assertIn("would each need their own layout switch or punch-in inside ~1.2 s", p)
        self.assertIn("Joins inside a takeover already up need neither", p)

    def test_picture_note_turns_full_face_on_for_the_whole_route(self):
        p = read(ROOT, ".claude", "skills", "claude-edit", "SKILL.md")
        self.assertIn("Set `allow_full_face` true and `allow_full_face_source` to his exact words in `RUN.md`, `beats.json` and `plan.json`.", p)
        self.assertIn("Hard-link `work/<id>/assets/face_full.mp4` into `work/<id>/v2/editorial/assets`", p)
        self.assertIn("If either changes before the build, re-run the plan.", p)
        self.assertIn("Only when RUN.md has allow_full_face true: rebuild face_full", p)

    def test_every_full_face_mention_is_gated(self):
        """A full-face line must name `full_face` itself, or sit under a rule line that does."""
        bare = []
        for folder, _, names in os.walk(TEMPLATES):
            for name in names:
                if not name.endswith(".md"):
                    continue
                path = os.path.join(folder, name)
                with open(path, encoding="utf-8") as f:
                    rule = ""
                    for n, line in enumerate(f, 1):
                        if re.match(r"\s*(- \*\*|\d+\. )|\||#", line):
                            rule = line
                        if re.search(r"full[- ]face|face_full", line, re.I) and "full_face" not in line and "full_face" not in rule:
                            bare.append(f"{os.path.relpath(path, ROOT)}:{n}: {line.strip()}")
        self.assertEqual(bare, [], "\n".join(bare))


if __name__ == "__main__":
    unittest.main(verbosity=2)
