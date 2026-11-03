"""Parallel recut workflow, run in node with stubbed agents (no edit or render).

Usage: python tools/tests/test_build_parallel.py
Harness follows test_full_face.py: async script body, same six injected APIs.
"""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools/workflows/next/recut-build-parallel.js"
HARNESS = r"""
import { readFileSync } from 'node:fs'
const [script, argsJson, repliesJson] = process.argv.slice(2)
const args = JSON.parse(argsJson), replies = JSON.parse(repliesJson)
const code = readFileSync(script, 'utf8').replace(/^export const meta/m, 'const meta')
const prompts = [], events = [], parallelCalls = []
let group = 0
const reply = (label) => {
  if (Object.hasOwn(replies, label)) {
    if (replies[label]?.__throw) throw new Error(replies[label].__throw)
    return replies[label]
  }
  if (label.startsWith('lead:')) return { ok: true, files: [], notes: '', chunks:
    Array.from({length: args?.chunks || 4}, (_, i) => ({id:'c'+(i+1), prefix:'c'+(i+1)+'-', start:i, end:i+1, beats:['b'+(i+1)]})) }
  if (label.startsWith('plancheck:')) return {ok:true, issues:[], warnings:[]}
  if (label.startsWith('integrate:')) return {lint_errors:0, motionlint:'ok', snaps_dir:'s', owner_audit:'PASS owners', source_check:'exit 3; no FAIL', whole_render:[], self_review:'checked'}
  return {ok:true, files:[], notes:''}
}
const agent = async (prompt, opts) => {
  const label = opts.label
  prompts.push({ label, prompt, schema: opts.schema })
  events.push(['start',label])
  await new Promise((resolve) => setTimeout(resolve, 3))
  try { return reply(label) } finally { events.push(['finish',label]) }
}
const parallel = async (thunks) => {
  const n = group++
  parallelCalls.push({group:n, count:thunks.length})
  events.push(['parallel-start',n])
  const result = await Promise.all(thunks.map((t) => t()))
  events.push(['parallel-finish',n])
  return result
}
const pipeline = (items, ...stages) => Promise.all(items.map(async (item) => {
  let r = item
  for (const stage of stages) r = await stage(r, item)
  return r
}))
const AsyncFunction = (async () => {}).constructor
const run = new AsyncFunction('agent', 'parallel', 'pipeline', 'phase', 'log', 'args', code)
try {
  const result = await run(agent,parallel,pipeline,()=>{},()=>{},{root: '/stub/root', ...args})  // the skill always passes root
  console.log(JSON.stringify({result,prompts,events,parallelCalls}))
} catch (e) { console.log(JSON.stringify({error:String(e),prompts,events,parallelCalls})) }
"""


def run_workflow(args=None, replies=None):
    with tempfile.TemporaryDirectory() as directory:
        harness = Path(directory) / "harness.mjs"
        harness.write_text(HARNESS, encoding="utf-8")
        result = subprocess.run(["node", str(harness), str(SCRIPT), json.dumps(args or {"id": "stub"}),
                                 json.dumps(replies or {})], capture_output=True, text=True,
                                encoding="utf-8", cwd=directory)
    if result.returncode:
        raise AssertionError(f"workflow failed in node:\n{result.stderr}")
    return json.loads(result.stdout)


def labels(run):
    return [p["label"] for p in run["prompts"]]


def prompts(run):
    return {p["label"]: p["prompt"] for p in run["prompts"]}


class ParallelBuild(unittest.TestCase):
    def test_stage_order_and_default_four_chunks(self):
        run = run_workflow()
        self.assertEqual(labels(run), ["lead:editorial", *[f"direct:editorial:c{i}" for i in range(1, 5)],
                         "merge-plan:editorial", "plancheck:editorial", "setup:editorial",
                         *[f"build:editorial:c{i}" for i in range(1, 5)], "merge-build:editorial", "integrate:editorial"])
        self.assertEqual([p["count"] for p in run["parallelCalls"]], [4, 4])
        self.assertFalse(run["result"][0]["refused"])
        self.assertEqual(run["result"][0]["build"]["owner_audit"], "PASS owners")

    def test_chunk_calls_overlap_in_both_parallel_stages(self):
        run = run_workflow({"id":"stub", "chunks":3})
        for role in ("direct", "build"):
            starts = [run["events"].index(["start",f"{role}:editorial:c{i}"]) for i in range(1,4)]
            finishes = [run["events"].index(["finish",f"{role}:editorial:c{i}"]) for i in range(1,4)]
            self.assertLess(max(starts), min(finishes))

    def test_plan_refusal_stops_before_setup(self):
        for check in (None, {}, {"ok":False,"issues":["bad fact"],"warnings":["ease"]},
                      {"ok":"true","issues":[]}, {"ok":True}, {"ok":True,"issues":["remaining"]}):
            with self.subTest(check=check):
                run = run_workflow(replies={"plancheck:editorial":check})
                self.assertTrue(run["result"][0]["refused"])
                self.assertNotIn("build", run["result"][0])
                self.assertNotIn("setup:editorial", labels(run))
                self.assertEqual(labels(run)[-1], "plancheck:editorial")

    def test_warnings_reach_every_builder_and_integrator(self):
        run = run_workflow(replies={"plancheck:editorial":{"ok":True,"issues":[],"warnings":["outline 6 px left"]}})
        self.assertFalse(run["result"][0]["refused"])
        for label, prompt in prompts(run).items():
            if label.startswith(("build:", "integrate:", "setup:")):
                self.assertIn("Plan-check warnings, not blockers", prompt)
                self.assertIn("outline 6 px left", prompt)

    def test_failed_chunk_retries_only_itself_once_before_merge(self):
        for failure in (None, {"ok":False,"notes":"broken fragment"}, {"__throw":"agent crashed"}):
            with self.subTest(failure=failure):
                run = run_workflow(replies={"build:editorial:c2":failure})
                calls = labels(run)
                self.assertEqual(calls.count("build:editorial:c2:retry"), 1)
                self.assertEqual(sum(label.endswith(":retry") for label in calls), 1)
                self.assertLess(calls.index("build:editorial:c2:retry"), calls.index("merge-build:editorial"))
                self.assertLess(calls.index("merge-build:editorial"), calls.index("integrate:editorial"))
                self.assertFalse(run["result"][0]["refused"])
                self.assertIn("First failure:", prompts(run)["build:editorial:c2:retry"])

    def test_failed_retry_stops_without_integrator(self):
        run = run_workflow(replies={"build:editorial:c2":{"ok":False},"build:editorial:c2:retry":None})
        self.assertTrue(run["result"][0]["refused"])
        self.assertNotIn("merge-build:editorial", labels(run))
        self.assertNotIn("integrate:editorial", labels(run))
        self.assertEqual(sum(label.endswith(":retry") for label in labels(run)), 1)

    def test_direction_chunk_also_retries_independently(self):
        run = run_workflow(replies={"direct:editorial:c3":None})
        self.assertIn("direct:editorial:c3:retry", labels(run))
        self.assertFalse(run["result"][0]["refused"])

    def test_failed_direction_retry_stops_before_merge_or_check(self):
        run = run_workflow(replies={"direct:editorial:c1":None,"direct:editorial:c1:retry":None})
        self.assertTrue(run["result"][0]["refused"])
        self.assertNotIn("merge-plan:editorial", labels(run))
        self.assertNotIn("plancheck:editorial", labels(run))

    def test_each_deterministic_step_fails_closed(self):
        for stage, absent in (("merge-plan:editorial","plancheck:editorial"),
                              ("setup:editorial","build:editorial:c1"),
                              ("merge-build:editorial","integrate:editorial")):
            with self.subTest(stage=stage):
                run = run_workflow(replies={stage:None})
                self.assertTrue(run["result"][0]["refused"])
                self.assertNotIn(absent, labels(run))

    def test_skip_direct_preserves_plan_but_rechecks(self):
        run = run_workflow({"id":"stub","skipDirect":True})
        self.assertEqual(labels(run)[:3], ["lead:editorial","plancheck:editorial","setup:editorial"])
        self.assertFalse(any(label.startswith("direct:") for label in labels(run)))
        self.assertIn("Do not change plan.json", prompts(run)["lead:editorial"])

    def test_plan_issues_take_precedence_and_preserve_events(self):
        run = run_workflow({"id":"stub","skipDirect":True,"planIssues":["fix bad highlight"]})
        self.assertIn("direct:editorial:c1", labels(run))
        for label, prompt in prompts(run).items():
            if label.startswith(("lead:","direct:")):
                self.assertIn("fix bad highlight", prompt)
                self.assertIn("event_id", prompt)
        self.assertNotIn("Plan-check issues:", prompts(run)["build:editorial:c1"])

    def test_unknown_style_refused_without_agents(self):
        run = run_workflow({"id":"stub","styles":["other"]})
        self.assertEqual(labels(run), [])
        self.assertTrue(run["result"][0]["refused"])

    def test_bad_chunk_count_or_lead_refuses(self):
        for count in (0, -1, 1.5, "4", 33):
            with self.subTest(count=count):
                run = run_workflow({"id":"stub","chunks":count})
                self.assertIn("chunks must be an integer", run["error"])
                self.assertEqual(labels(run), [])
        for lead in (None, {"ok":True,"chunks":[]}, {"ok":True,"chunks":[{"id":"../bad"}]}):
            with self.subTest(lead=lead):
                run = run_workflow(replies={"lead:editorial":lead})
                self.assertTrue(run["result"][0]["refused"])
                self.assertEqual(labels(run), ["lead:editorial"])

    def test_gate_and_full_qa_contracts_survive(self):
        p = prompts(run_workflow())
        for needle in ("issues are blockers only", "When unsure which list, warn.", "geometry.py measures those on the built page"):
            self.assertIn(needle, p["plancheck:editorial"])
        for needle in ("build.py", "--audit", "--all", "exit 3 is expected", "Exit 4", "hyperframes lint", "motionlint.py", "hyperframes snapshot", "Do NOT render"):
            self.assertIn(needle, p["integrate:editorial"])
        for i in range(1,5):
            self.assertIn(f"tools_local/chunks/c{i}/", p[f"build:editorial:c{i}"])
            self.assertIn("No assembled sources", p[f"build:editorial:c{i}"])
            self.assertIn(f"--check-chunk c{i}", p[f"build:editorial:c{i}"])

    def test_settings_notes_and_image_ownership(self):
        for enabled in (False, True):
            run = run_workflow({"id":"stub","allowFullFace":enabled,"allowFullFaceSource":"his words","codex":True,"note":"keep this note"})
            p = prompts(run)
            for label, prompt in p.items():
                self.assertIn("allow_full_face " + str(enabled).lower(), prompt, label)
                self.assertIn("keep this note", prompt, label)
            self.assertIn("codex exec", p["lead:editorial"])
            self.assertIn("never generate images or write ASSETS.md", p["direct:editorial:c1"])
            if enabled:
                self.assertIn("--full-face", p["setup:editorial"])
            else:
                self.assertIn("Leave face_full.mp4 out", p["setup:editorial"])


    def test_integrator_crash_is_a_refusal(self):
        for failure in (None, {"__throw":"QA crashed"}):
            with self.subTest(failure=failure):
                run = run_workflow(replies={"integrate:editorial":failure})
                self.assertTrue(run["result"][0]["refused"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
