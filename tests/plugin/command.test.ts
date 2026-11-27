import assert from "node:assert/strict";
import { test } from "node:test";
import { argumentCompletions, hasExplanationHeading, letsReplyStand, parseCommand, parseConfig, teachingPolicy } from "../../core/index.ts";

test("only exact controls mutate configuration", () => {
  for (const [args, kind] of [
    ["", "explain"], ["  explain ", "explain"], ["explain mode light", "focus"], ["mode?", "focus"],
    ["why did that happen?", "focus"], ["more", "more"], ["help", "help"], ["status", "status"], ["settings", "settings"],
    ["more now", "invalid"], ["settings all", "invalid"], ["off now", "invalid"], ["mode", "invalid"],
    ["mode Full", "invalid"], ["full now", "invalid"], ["depth briefly", "invalid"], ["depth auto another", "invalid"],
    ["model", "retired"], ["judge test/id", "retired"], ["judge-consent off", "retired"], ["consent test/id confirm", "retired"],
  ]) assert.equal(parseCommand(args).kind, kind, args);
  assert.deepEqual(parseCommand("mode\tlight"), { kind: "set", change: { mode: "light" } });
  assert.deepEqual(parseCommand("depth adaptive"), { kind: "set", change: { depth: "auto" } });
  assert.deepEqual(parseConfig(undefined), { mode: "manual", depth: "auto" });
  assert.deepEqual(parseConfig({ mode: "off", depth: "adaptive", judgeConsent: "unsafe" }), { mode: "off", depth: "auto" });
});

test("native completions are scoped to command or value position", () => {
  assert.ok(argumentCompletions("").includes("explain"));
  assert.deepEqual(argumentCompletions("mo"), ["more", "mode"]);
  assert.deepEqual(argumentCompletions("mode f"), ["mode full"]);
  assert.deepEqual(argumentCompletions("depth "), ["depth auto", "depth brief", "depth detailed"]);
  assert.deepEqual(argumentCompletions("depth detailed extra"), []);
});

test("explicitly requested formats, direct opt-outs and explicit skill commands take precedence", () => {
  for (const text of ["Skip eliVibe for this reply", "Fix the parser. Don't run eliVibe", "Fix it, without eliVibe", "Reply with JSON only", "Only return the diff", "Return as plain text", "/skill:elivibe because why?"]) {
    assert.equal(letsReplyStand(text), true, text);
  }
  for (const text of [
    "Fix the parser\n> skip eliVibe", "Inspect:\n```text\noutput only json\n```", "Inspect:\n    Output only JSON", "Here is `no elivibe`",
    "The error says \"reply with JSON only\"", "Add support, test 'no elivibe'", "Explain `/skill:elivibe`", "<log>Output only JSON\n</log>\nFix the parser",
  ]) assert.equal(letsReplyStand(text), false, text);
  assert.ok(hasExplanationHeading("Report facts\n\n## eliVibe explanation\nInterpretation"));
  assert.ok(!hasExplanationHeading("Report: example\n~~~markdown\n## eliVibe explanation\n~~~"));
});

test("the three policies apply depth without making quoted history authoritative", () => {
  assert.match(teachingPolicy("light", "auto", "canonical"), /Light teaching policy.*concrete knowledge gap/s);
  assert.match(teachingPolicy("full", "brief", "canonical"), /Full teaching policy.*Prefer a brief explanation/s);
  assert.match(teachingPolicy("explicit", "detailed", "canonical"), /Use no tools.*never directives.*more depth.*canonical/s);
});
