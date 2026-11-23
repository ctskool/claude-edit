"""Full-face gate for /claude-edit: motionlint and the template rule files.

Usage: python tools/tests/test_full_face.py
run_workflow and dry_run run a workflow script in node with agent, parallel, pipeline, phase, log and args stubbed, and capture its
prompts. The sound step's test uses them. The plan and build workflows they were written for were archived on 2026-11-12
(retired 2026-11-12, not shipped), with their cases.
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
        # The build runs motionlint on index.html from inside the project.
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


def read(*parts):
    with open(os.path.join(*parts), encoding="utf-8") as f:
        return f.read()


def skill_text():
    """The skill: SKILL.md (the router) followed by its side files."""
    folder = os.path.join(ROOT, ".claude", "skills", "claude-edit")
    names = ["SKILL.md"] + sorted(n for n in os.listdir(folder) if n.endswith(".md") and n != "SKILL.md")
    return "\n".join(read(folder, n) for n in names)


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
        p = skill_text()
        self.assertIn("Set `allow_full_face` true and `allow_full_face_source` to his exact words in `RUN.md`, `beats.json` and `plan.json`.", p)
        self.assertIn("Hard-link `work/<id>/assets/face_full.mp4` into `work/<id>/v2/editorial/assets`", p)
        self.assertIn("If either changes before the build, re-run the plan.", p)
        self.assertIn("Only when RUN.md has allow_full_face true: rebuild face_full", p)

    def test_every_full_face_mention_is_gated(self):
        """A full-face line must name `full_face` itself, or sit under a rule line that does.

        Rule files only. A template's library/ is skipped: tools/library.py harvests it from approved edits, and its
        "For:" lines are records of what one video did and why (often why it did not go full-face), not instructions."""
        bare = []
        for folder, _, names in os.walk(TEMPLATES):
            if "library" in os.path.relpath(folder, TEMPLATES).split(os.sep):
                continue
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
