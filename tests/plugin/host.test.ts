// Copyright (c) 2026 Tai Benvenuti
// SPDX-License-Identifier: GPL-3.0-only

import assert from "node:assert/strict";
import { test } from "node:test";
import type { ExtensionAPI } from "@oh-my-pi/pi-coding-agent";
import elivibe from "../../adapters/omp/index.ts";

const source = "The parser rejects invalid entries. A targeted test passed, but production deployment has not been verified.";
const explanation = "## eliVibe explanation\nThe targeted test does not exercise the production deployment.";

type Content = { type: "text"; text: string }[];
type Message = { role: string; content: string | Content; attribution?: string; timestamp?: number; [key: string]: unknown };
type Entry = { type: string; id: string; message?: Message; [key: string]: unknown };
type Hooks = { messages?: Message[]; message?: Omit<Message, "role">; block?: boolean; reason?: string; systemPrompt?: string[] };
type Completion = NonNullable<Parameters<ExtensionAPI["registerCommand"]>[1]["getArgumentCompletions"]>;

function host() {
  let now = 0;
  let isIdle = true;
  let pending = false;
  let model = "host-model";
  let session = "a";
  let branch: Entry[] = [];
  const messages: Message[] = [];
  const notices: string[] = [];
  const submissions: { prompt: string; options: unknown }[] = [];
  const requests: { messages: Message[]; systemPrompt: string[]; model: string }[] = [];
  let systemPrompt = ["host policy"];
  const events = new Map<string, (event: object, context: object) => Hooks | undefined>();
  let command: (args: string, ctx: object) => Promise<void>;
  let complete: Completion;
  let select: string | undefined;
  let aborts = 0;
  let failApplied = false;
  let send: (text: string) => void | Promise<void>;
  const ctx = {
    agent: { id: "Main", kind: "main" }, mode: "tui", hasUI: true,
    isIdle: () => isIdle, hasPendingMessages: () => pending, abort: () => { aborts++; },
    models: { current: () => model && { id: model } },
    ui: { notify: (text: string) => notices.push(text), select: async () => select },
    sessionManager: { getLeafId: () => branch.at(-1)?.id ?? null, getBranch: () => branch, getSessionId: () => session },
  };
  const emit = (name: string, event = {}) => events.get(name)?.(event, ctx);
  function push(message: Message) {
    messages.push(message);
    const id = `entry-${++now}`;
    if (message.role === "custom") branch.push({ ...message, type: "custom_message", id });
    else branch.push({ type: "message", id, message });
    return id;
  }
  function answer(text = source, stopReason = "stop") {
    return push({ role: "assistant", content: [{ type: "text", text }], stopReason, timestamp: now + 1, model, provider: "test" });
  }
  function start(text: string, { actual = text, attribution = "user", steering = false } = {}) {
    const priorAborts = aborts;
    const setup = emit("before_agent_start", { reason: "prompt", prompt: text, systemPrompt: ["host policy"] });
    if (aborts !== priorAborts) return;
    systemPrompt = setup?.systemPrompt ?? ["host policy"];
    push({ role: "user", content: actual, attribution, steering });
    if (setup?.message) push({ ...setup.message, role: "custom" } as Message);
    return wire();
  }
  function wire(payload = messages) {
    const priorAborts = aborts;
    const provider = emit("context", { messages: payload })?.messages ?? payload;
    if (aborts !== priorAborts) return;
    requests.push({ messages: [...provider], systemPrompt, model });
    return systemPrompt[1];
  }
  function end(willContinue = false) {
    emit("agent_end", { willContinue, messages });
    if (!willContinue) systemPrompt = ["host policy"];
  }
  send = text => { start(text); answer(explanation); end(); };
  elivibe({
    on: (name: string, handler: (event: object, context: object) => Hooks | undefined) => events.set(name, handler),
    registerCommand: (name: string, registration: { handler: typeof command; getArgumentCompletions: Completion }) => {
      assert.equal(name, "elivibe");
      command = registration.handler;
      complete = registration.getArgumentCompletions;
    },
    appendEntry: (customType: string, data: unknown) => {
      if (failApplied && customType === "elivibe-applied") throw new Error("Session write failed");
      branch.push({ type: "custom", id: `entry-${++now}`, customType, data });
    },
    sendUserMessage: async (prompt: string, options: unknown) => {
      submissions.push({ prompt, options });
      await send(prompt);
    },
  } as unknown as ExtensionAPI);
  emit("session_start");
  return {
    emit, ctx, messages, notices, submissions, requests, answer, start, wire, end, push,
    policy: () => requests.at(-1)?.systemPrompt[1] ?? "",
    command: (args = "") => command(args, ctx), complete: (prefix: string) => complete(prefix),
    get branch() { return branch; }, get aborts() { return aborts; },
    set model(value: string) { model = value; }, set isIdle(value: boolean) { isIdle = value; },
    set pending(value: boolean) { pending = value; }, set select(value: string | undefined) { select = value; },
    set failApplied(value: boolean) { failApplied = value; },
    set send(value: typeof send) { send = value; },
    switchBranch(value: Entry[], event = "session_tree") {
      branch = value;
      messages.length = 0;
      for (const entry of value) {
        if (entry.message) messages.push(entry.message);
        else if (entry.type === "custom_message") messages.push(entry as unknown as Message);
      }
      emit(event);
    },
    switchSession() { session = "b"; branch = []; messages.length = 0; emit("session_switch"); },
  };
}

test("first use help, readiness, exact controls, and optional settings never dispatch", async () => {
  const h = host();
  await h.command("help");
  assert.match(h.notices.at(-1)!, /^\/elivibe — explain/);
  await h.command();
  assert.match(h.notices.at(-1)!, /No completed handoff/);
  await h.command("more");
  assert.match(h.notices.at(-1)!, /No eliVibe explanation/);
  h.model = "";
  await h.command("status");
  assert.match(h.notices.at(-1)!, /manual mode, auto depth.*\/model/);
  await h.command("why did the deployment fail?");
  assert.match(h.notices.at(-1)!, /\/model/);
  await h.command("depth auto extra");
  assert.match(h.notices.at(-1)!, /Invalid/);
  await h.command("judge-consent test/model confirm");
  assert.match(h.notices.at(-1)!, /retired/);
  await h.command("settings");
  assert.equal(h.branch.length, 0);
  h.select = "mode light";
  await h.command("settings");
  assert.deepEqual(h.branch.at(-1)?.data, { mode: "light", depth: "auto" });
  h.ctx.hasUI = false;
  await h.command("settings");
  assert.match(h.notices.at(-1)!, /depth auto\|brief\|detailed/);
  assert.deepEqual(h.submissions, []);
  assert.deepEqual(h.complete("depth d"), [{ value: "depth detailed", label: "depth detailed" }]);
});

test("explicit requests work in Off and Full and use attributed ordinary context", async () => {
  const h = host();
  const id = h.answer();
  await h.command("off");
  await h.command();
  assert.deepEqual(h.submissions[0], { prompt: "/elivibe", options: { attribution: "user" } });
  const provider = h.requests.at(-1)!;
  assert.equal(provider.systemPrompt[0], "host policy");
  assert.match(h.policy(), /explicit explanation.*selected source is assistant message 1/s);
  assert.ok(!h.policy().includes(source));
  assert.deepEqual(provider.messages[0], h.branch.find(entry => entry.id === id)?.message);
  assert.equal(provider.messages.at(-1)?.role, "user");
  assert.equal(provider.messages.at(-1)?.attribution, "user");
  assert.ok(!provider.messages.some(message => message.customType === "elivibe-turn"));
  await h.command("full");
  await h.command("explain mode differences");
  assert.equal(h.submissions.at(-1)?.prompt, "/elivibe explain mode differences");
  assert.match(h.policy(), /explicit explanation/);
  await h.command("status");
  assert.match(h.notices.at(-1)!, /full mode/);
});

test("More keeps the source through repeated explanations, follow-up, and branch replay", async () => {
  const h = host();
  h.answer();
  const untreated = [...h.branch];
  await h.command();
  h.start("Tell me more about that");
  h.answer("The fixture is not the deployed service.");
  h.end();
  await h.command("more");
  assert.match(h.policy(), /selected source is assistant message 1.*Deepen assistant message 2/s);
  await h.command("more");
  assert.match(h.policy(), /selected source is assistant message 1.*Deepen assistant message 4/s);
  const treated = [...h.branch];
  h.switchBranch(untreated);
  await h.command("more");
  assert.match(h.notices.at(-1)!, /No eliVibe explanation/);
  h.switchBranch(treated);
  await h.command("more");
  assert.match(h.policy(), /selected source is assistant message 1.*Deepen assistant message 5/s);
});

test("an explicit explanation with a failed session write never becomes a handoff", async () => {
  const h = host();
  h.answer();
  await h.command();
  h.start("Check the deployment");
  h.answer("Production deployment is still pending.");
  h.end();
  h.failApplied = true;
  await h.command();
  assert.match(h.policy(), /selected source is assistant message 3/);
  assert.deepEqual(h.messages.at(-1)?.content, [{ type: "text", text: explanation }]);
  await h.command("more");
  assert.match(h.notices.at(-1)!, /No eliVibe explanation/);
  assert.equal(h.submissions.length, 2);
  await h.command();
  assert.match(h.policy(), /selected source is assistant message 3/);
});

test("bare uses the latest completed ordinary answer while More keeps its source", async () => {
  const h = host();
  h.answer();
  await h.command();
  await h.command("off");
  h.start("Return a report in Off mode.");
  h.answer("New report.");
  h.end();
  h.start("Try another approach");
  h.answer("Incomplete attempt.", "aborted");
  h.end();
  h.push({ role: "custom", customType: "skill-prompt", attribution: "user", display: true,
    details: { name: "elivibe" }, content: "Standalone eliVibe invocation" });
  h.answer("Standalone explanation.");
  h.end();
  await h.command("more");
  assert.match(h.policy(), /selected source is assistant message 1.*Deepen assistant message 2/s);
  await h.command();
  assert.match(h.policy(), /selected source is assistant message 3/);
});

test("in-turn automatic teaching honors delivered payload and never adds a turn", async () => {
  const h = host();
  assert.equal(h.start("Fix the parser"), undefined);
  h.answer(); h.end();
  await h.command("light");
  assert.match(h.start("Fix the parser")!, /Light teaching policy/);
  h.answer(`${source}\n\n${explanation}`); h.end();
  assert.equal(h.submissions.length, 0);
  await h.command("more");
  assert.match(h.policy(), /selected source is assistant message 2.*Deepen assistant message 2/s);
  await h.command("full");
  assert.equal(h.start("Return only JSON"), undefined);
  const appliedEntries = () => h.branch.filter(entry => entry.customType === "elivibe-applied").length;
  const count = appliedEntries();
  h.start("Fix the parser", { actual: "Return only JSON" });
  h.start("Fix the parser", { attribution: "agent" });
  h.start("Fix the parser", { steering: true });
  assert.equal(appliedEntries(), count);
  assert.match(h.start("Fix the parser\n> Return only JSON")!, /Full teaching policy/);
});

test("compaction and intrinsically source-less explanations do not select another report", async () => {
  const h = host();
  await h.command("what is an outbox?");
  await h.command("more");
  assert.match(h.notices.at(-1)!, /No eliVibe explanation/);
  h.answer();
  await h.command();
  const last = h.branch.at(-1)!.id;
  h.branch.push({ id: "compact", type: "compaction", firstKeptEntryId: last });
  await h.command("more");
  assert.match(h.notices.at(-1)!, /No eliVibe explanation/);
  await h.command();
  assert.match(h.notices.at(-1)!, /No completed handoff/);
});

test("admission is exclusive and an explicit tool veto survives a filtered marker", async () => {
  const h = host();
  const { promise, resolve } = Promise.withResolvers<void>();
  h.answer();
  h.send = async text => {
    h.start(text);
    const filtered = h.messages.filter(message => message.customType !== "elivibe-turn");
    assert.match(h.wire(filtered)!, /explicit explanation/);
    assert.equal(h.emit("tool_call")?.block, true);
    h.end(true);
    assert.equal(h.emit("tool_call")?.block, true);
    await promise;
    h.answer("cancelled", "aborted");
    h.end();
  };
  const running = h.command();
  await h.command("more");
  assert.match(h.notices.at(-1)!, /Wait for OMP/);
  resolve();
  await running;
  assert.equal(h.emit("tool_call"), undefined);
  assert.equal(h.wire(), undefined);
  assert.equal(h.start("/elivibe"), undefined);
  assert.equal(h.emit("tool_call"), undefined);
});

test("foreign dispatched text cannot use an explicit request's authority", async () => {
  const h = host();
  h.answer();
  h.send = text => {
    assert.equal(h.start(text, { actual: "Different work" }), undefined);
    assert.equal(h.aborts, 1);
    assert.equal(h.emit("tool_call")?.block, true);
    h.switchSession();
    assert.equal(h.emit("tool_call"), undefined);
  };
  await h.command();
});

test("an opt-out answer cannot become an eliVibe interpretation by copying the heading", async () => {
  const h = host();
  await h.command("full");
  assert.equal(h.start("Return only markdown"), undefined);
  h.answer(explanation);
  h.end();
  await h.command("more");
  assert.match(h.notices.at(-1)!, /No eliVibe explanation/);
});

test("an automatic heading with a failed session write remains part of the ordinary handoff", async () => {
  const h = host();
  await h.command("light");
  h.failApplied = true;
  assert.match(h.start("Fix the parser")!, /Light teaching policy/);
  h.answer(`${source}\n\n${explanation}`);
  h.end();
  await h.command("more");
  assert.match(h.notices.at(-1)!, /No eliVibe explanation/);
  await h.command();
  assert.match(h.policy(), /selected source is assistant message 1/);
  assert.doesNotMatch(h.policy(), /report before the eliVibe heading/);
});

test("a request whose source disappears in preparation cannot substitute a different report", async () => {
  const h = host();
  h.answer();
  h.send = text => {
    h.messages.length = 0;
    assert.equal(h.start(text), undefined);
    assert.match(h.notices.at(-1)!, /selected handoff changed.*Paste the handoff/);
    assert.equal(h.requests.length, 0);
    assert.equal(h.emit("tool_call")?.block, true);
    h.end();
  };
  await h.command();
});

test("explicit requests cannot trigger implicit @file reads or ^model expansion", async () => {
  const h = host();
  for (const prompt of ["please explain @secret.txt", "explain why ^model changed the answer"]) {
    await h.command(prompt);
    assert.match(h.notices.at(-1)!, /Paste the relevant text/);
  }
  assert.deepEqual(h.submissions, []);
});

test("the host rewriting an admitted prompt is refused once and does not veto later work", async () => {
  const h = host();
  h.answer();
  h.send = () => {
    assert.equal(h.start('/elivibe Explain <model agent=\"m1\" name=\"alias\"/>'), undefined);
    throw new Error("PromptDroppedError");
  };
  await h.command("Explain an alias");
  assert.equal(h.requests.length, 0);
  assert.deepEqual(h.notices, ["OMP changed or queued the explanation request before dispatch. Wait for OMP to finish, then retry /elivibe."]);
  h.start("Work on another ordinary task");
  assert.equal(h.requests.length, 1);
  assert.equal(h.emit("tool_call"), undefined);
});

test("hollow cancelled turns do not shift a retained source and the active model owns the new turn", async () => {
  const h = host();
  h.answer("", "aborted");
  const original = h.answer();
  h.model = "replacement-model";
  await h.command();
  assert.match(h.policy(), /selected source is assistant message 1 \(count only assistant messages with visible text or tool calls/);
  assert.equal(h.requests.at(-1)?.model, "replacement-model");
  assert.equal(h.branch.find(entry => entry.id === original)?.message?.model, "host-model");
});

test("an earlier visible cancellation can be bypassed by anchoring from the current user request", async () => {
  const h = host();
  h.answer("A visible partial response", "aborted");
  h.answer();
  h.send = text => {
    h.messages.shift();
    assert.match(h.start(text)!, /count backward from the current user request to assistant message 1/);
    h.end();
  };
  await h.command();
  assert.equal(h.requests.length, 1);
});

test("a source between visible incomplete replies cannot be located reliably", async () => {
  const h = host();
  h.answer("A visible partial response", "aborted");
  h.answer();
  h.answer("Another visible partial response", "aborted");
  h.send = text => {
    assert.equal(h.start(text), undefined);
    throw new Error("PromptDroppedError");
  };
  await h.command();
  assert.equal(h.requests.length, 0);
  assert.match(h.notices.at(-1)!, /cannot be located reliably.*Paste it/);
  assert.equal(h.notices.length, 1);
});

test("session preferences migrate without credentials and explicit readiness failures are actionable", async () => {
  const h = host();
  h.branch.push({ type: "custom", id: "old", customType: "elivibe-settings", data: { mode: "light", depth: "adaptive", consent: "legacy", model: "legacy" } });
  await h.command("status");
  assert.match(h.notices.at(-1)!, /light mode, auto depth/);
  await h.command("depth brief");
  assert.deepEqual(h.branch.at(-1)?.data, { mode: "light", depth: "brief" });
  h.switchSession();
  await h.command("status");
  assert.match(h.notices.at(-1)!, /manual mode, auto depth/);
  h.send = () => { throw new Error("do not disclose provider details"); };
  await h.command("question");
  assert.match(h.notices.at(-1)!, /could not start.*\/model/);
  assert.ok(!h.notices.at(-1)!.includes("provider details"));
  h.isIdle = false;
  await h.command("question");
  assert.match(h.notices.at(-1)!, /Wait for OMP/);
  h.isIdle = true; h.pending = true;
  await h.command("question");
  assert.match(h.notices.at(-1)!, /Wait for OMP/);
});
