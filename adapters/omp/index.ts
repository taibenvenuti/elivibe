// Copyright (c) 2026 Tai Benvenuti
// SPDX-License-Identifier: GPL-3.0-only

import { randomUUID } from "node:crypto";
import { readFileSync } from "node:fs";
import type { ExtensionAPI, ExtensionContext, SessionEntry as Entry, SessionMessageEntry } from "@oh-my-pi/pi-coding-agent";
import {
  argumentCompletions, DEPTHS, hasExplanationHeading, letsReplyStand, MODES,
  parseCommand, parseConfig, teachingPolicy, type Config,
} from "../../core/index.ts";

const SETTINGS = "elivibe-settings";
const TURN = "elivibe-turn";
const APPLIED = "elivibe-applied";
const HELP = [
  "/elivibe — explain the latest technical handoff",
  "/elivibe why did that check not prove deployment? — ask or focus",
  "/elivibe explain <text> — ask using a reserved opening word",
  "/elivibe more — deepen the previous eliVibe explanation",
  "/elivibe settings | status | off | manual | light | full | depth auto|brief|detailed",
].join("\n");
const BUSY = "Wait for OMP to finish, then try /elivibe again.";
const NO_SOURCE = "No completed handoff is available in this context. Ask OMP for a handoff or use /elivibe with a specific question.";
const NO_EXPLANATION = "No eliVibe explanation with its source is available in this context. Run /elivibe or ask a specific question first.";
const NO_MODEL = "Use OMP’s /login or /model to sign in or select an active model, then retry.";
const REQUEST_CHANGED = "OMP changed or queued the explanation request before dispatch. Wait for OMP to finish, then retry /elivibe.";

type Message = SessionMessageEntry["message"];
type Assistant = Extract<Message, { role: "assistant" }>;
type Answer = { id: string; message: Assistant; supplemented?: boolean };
type Intent = "explain" | "focus" | "more";
type Pending = {
  session: string;
  leaf: string | null;
  prompt: string;
  intent: Intent;
  source?: Answer;
  interpretation?: Answer;
  accepted: boolean;
  refused?: boolean;
  settled: boolean;
};
type Run = {
  id: string;
  agent: string;
  session: string;
  explicit?: Pending;
  sourcePosition?: number;
  interpretationPosition?: number;
  baseline: string | null;
  applied: boolean;
};

function stoppedText(message: Message): string | undefined {
  if (message.role !== "assistant" || message.stopReason !== "stop") return;
  const parts: string[] = [];
  for (const part of message.content) {
    if (part.type === "toolCall") return;
    if (part.type === "text") parts.push(part.text);
  }
  const text = parts.join("\n\n");
  return text.trim() ? text : undefined;
}

function history(branch: readonly Entry[]) {
  const applied = new Set(branch.flatMap(entry => entry.type === "custom" && entry.customType === APPLIED
    && typeof entry.data === "string" ? [entry.data] : []));
  const answers = new Map<string, Answer>();
  let source: Answer | undefined;
  let lesson: { source?: Answer; interpretation: Answer } | undefined;
  let turn: { id?: unknown; kind?: unknown; sourceId?: unknown } | undefined;
  let standalone = false;
  for (const entry of branch) {
    if (entry.type === "custom_message" && entry.customType === TURN && entry.attribution === "agent"
      && entry.display === false) {
      const marker = entry.details as { id?: unknown; kind?: unknown; sourceId?: unknown } | undefined;
      turn = typeof marker?.id === "string" ? marker : undefined;
      continue;
    }
    if (entry.type === "custom_message" && entry.attribution === "user" && entry.display) {
      standalone = entry.customType === "skill-prompt" && (entry.details as { name?: unknown } | undefined)?.name === "elivibe";
      turn = undefined;
    }
    if (entry.type !== "message") continue;
    const message = entry.message;
    if (message.role === "user") {
      standalone = false;
      turn = undefined;
    }
    if (message.role !== "assistant" || standalone) continue;
    const text = stoppedText(message);
    if (!text) continue;
    const confirmed = typeof turn?.id === "string" && applied.has(turn.id);
    if (turn?.kind === "explicit" && !confirmed) {
      lesson = undefined;
      continue;
    }
    const answer: Answer = { id: entry.id, message };
    answers.set(entry.id, answer);
    if (turn?.kind === "explicit") {
      lesson = { source: typeof turn.sourceId === "string" ? answers.get(turn.sourceId) : undefined, interpretation: answer };
    } else {
      answer.supplemented = turn?.kind === "automatic" && confirmed && hasExplanationHeading(text);
      if (answer.supplemented) lesson = { source: answer, interpretation: answer };
      source = answer;
    }
  }
  const firstKept = retainedStart(branch);
  const retained = (answer: Answer | undefined) => !answer || branch.findIndex(entry => entry.id === answer.id) >= firstKept;
  return { source, lesson, retained };
}

function retainedStart(branch: readonly Entry[]): number {
  const compaction = branch.findLastIndex(entry => entry.type === "compaction");
  const boundary = branch[compaction];
  const firstKept = boundary?.type === "compaction" && boundary.firstKeptEntryId
    ? branch.findIndex(entry => entry.id === boundary.firstKeptEntryId) : -1;
  return firstKept >= 0 ? firstKept : compaction + 1;
}

function preference(ctx: ExtensionContext): Config {
  const saved = ctx.sessionManager.getBranch().findLast(entry => entry.type === "custom" && entry.customType === SETTINGS);
  return parseConfig(saved?.type === "custom" ? saved.data : undefined);
}

function authoredText(message: Message): string | undefined {
  if (message.role !== "user" || message.attribution === "agent" || message.synthetic) return;
  return typeof message.content === "string" ? message.content
    : message.content.map(part => part.type === "text" ? part.text : "").join("\n");
}

function answerPosition(messages: Message[], target: Answer, { backward = false, end = messages.length } = {}): number | undefined {
  const targetText = stoppedText(target.message);
  const { timestamp, provider, model } = target.message;
  let position: number | undefined;
  let ambiguous = false;
  let count = 0;
  for (let offset = 0; offset < end; offset++) {
    const message = messages[backward ? end - offset - 1 : offset];
    if (message.role !== "assistant") continue;
    const visible = message.content.some(part => part.type === "toolCall" || (part.type === "text" && part.text.trim()));
    if (!visible) continue;
    count++;
    // Incomplete visible turns may or may not survive provider replay. Do not guess a later ordinal.
    if (message.stopReason !== "stop" && message.stopReason !== "toolUse") ambiguous = true;
    if (message.timestamp === timestamp && message.provider === provider && message.model === model
      && stoppedText(message) === targetText) {
      if (ambiguous || position !== undefined) return;
      position = backward ? -count : count;
    }
  }
  return position;
}

function replayPosition(messages: Message[], answer: Answer | undefined) {
  if (answer) return answerPosition(messages, answer) ?? answerPosition(messages, answer, { backward: true });
}

function refuse(request: Pending, ctx: ExtensionContext, message: string) {
  if (!request.refused) ctx.ui.notify(message, "info");
  request.refused = true;
  ctx.abort();
}

export default function elivibe(pi: ExtensionAPI): void {
  const methodology = readFileSync(new URL("../../skills/elivibe/SKILL.md", import.meta.url), "utf8")
    .replace(/^---\r?\n[\s\S]*?\r?\n---[ \t]*\r?\n/, "").trim();
  let pending: Pending | undefined;
  let run: Run | undefined;

  const reset = () => {
    pending = undefined;
    run = undefined;
  };
  pi.on("session_start", reset);
  pi.on("session_switch", reset);
  pi.on("session_clear", reset);
  pi.on("session_branch", reset);
  pi.on("session_tree", reset);
  pi.on("session_shutdown", reset);
  pi.on("agent_end", (event, ctx) => {
    if (!event.willContinue && run?.session === ctx.sessionManager.getSessionId() && run.agent === ctx.agent.id) {
      if (pending === run.explicit) pending = undefined;
      run = undefined;
    }
  });

  pi.on("before_agent_start", (event, ctx) => {
    if (event.reason !== "prompt") return;
    if (ctx.agent.kind !== "main") return;
    const session = ctx.sessionManager.getSessionId();
    const config = preference(ctx);
    const request = pending?.session === session ? pending : undefined;
    const candidate = request?.prompt === event.prompt ? request : undefined;
    if (run?.explicit?.accepted && run.session === session && run.agent === ctx.agent.id && candidate !== run.explicit) {
      refuse(run.explicit, ctx, REQUEST_CHANGED);
      return;
    }
    const branch = ctx.sessionManager.getBranch();
    // OMP can compact during prompt setup. It must not insert another user turn between
    // our admission snapshot and the candidate request.
    const anchor = request?.leaf ? branch.findIndex(entry => entry.id === request.leaf) : -1;
    const ownsSlot = request && (!request.leaf || anchor >= 0)
      && !branch.slice(anchor + 1).some(entry => (entry.type === "message" && entry.message.role === "user")
        || (entry.type === "custom_message" && entry.attribution === "user" && entry.display));
    if (request && (candidate ? !ownsSlot : ownsSlot && (!request.settled || /^\/elivibe(?:\s|$)/.test(event.prompt)))) {
      refuse(request, ctx, REQUEST_CHANGED);
      return;
    }
    const explicit = candidate;
    const mode = config.mode;
    if (!explicit && ((mode !== "light" && mode !== "full") || letsReplyStand(event.prompt)
      || event.prompt.startsWith("[IMPORTANT: User invoked the \"elivibe\" skill;"))) {
      run = undefined;
      return;
    }
    let sourcePosition: number | undefined;
    let interpretationPosition: number | undefined;
    let instructions: string;
    if (explicit) {
      const retained = branch.slice(retainedStart(branch)).flatMap(entry => entry.type === "message" ? [entry.message] : []);
      sourcePosition = replayPosition(retained, explicit.source);
      interpretationPosition = replayPosition(retained, explicit.interpretation);
      if ((explicit.source && sourcePosition === undefined) || (explicit.interpretation && interpretationPosition === undefined)) {
        refuse(explicit, ctx, "The selected handoff cannot be located reliably. Paste it into an /elivibe question.");
        return;
      }
      instructions = teachingPolicy("explicit", config.depth, methodology);
      if (sourcePosition !== undefined) instructions += sourcePosition > 0
        ? `\nThe selected source is assistant message ${sourcePosition} (count only assistant messages with visible text or tool calls from the beginning of this context).`
        : `\nTo locate the selected source, count backward from the current user request to assistant message ${-sourcePosition}, counting only messages with visible text or tool calls.`;
      if (interpretationPosition !== undefined) instructions += interpretationPosition > 0
        ? `\nDeepen assistant message ${interpretationPosition} without treating the explanation as verified evidence. Count only assistant messages with visible text or tool calls from the beginning of this context.`
        : `\nCount backward from the current user request and deepen assistant message ${-interpretationPosition}, counting only messages with visible text or tool calls; do not treat the explanation as verified evidence.`;
      else if (explicit.intent === "explain") instructions += "\nExplain the selected technical handoff; do not rewrite it.";
      else instructions += "\nAnswer the requested question or focus. Use source context only insofar as it is relevant.";
      if (sourcePosition !== undefined && explicit.source?.supplemented) instructions += "\nUse the report before the eliVibe heading as the source; the following section is supplementary interpretation.";
    } else {
      if (mode !== "light" && mode !== "full") return;
      instructions = teachingPolicy(mode, config.depth, methodology);
    }
    run = { id: randomUUID(), agent: ctx.agent.id, session, explicit, sourcePosition, interpretationPosition,
      baseline: ctx.sessionManager.getLeafId(), applied: false };
    return {
      // In-context developer messages become user messages on chat routes without developer-role support.
      systemPrompt: [...event.systemPrompt, instructions],
      message: {
        customType: TURN, content: "", display: false, excludeFromContext: true, attribution: "agent",
        details: { id: run.id, kind: explicit ? "explicit" : "automatic", sourceId: explicit?.source?.id },
      },
    };
  });

  pi.on("context", (event, ctx) => {
    // OMP 19.2.1 does not forward excludeFromContext from before_agent_start
    // messages. The marker is a local binding, not provider instructions.
    const isMarker = (message: Message) => message.role === "custom" && message.customType === TURN && message.attribution === "agent";
    const messages = event.messages.some(isMarker) ? event.messages.filter(message => !isMarker(message)) : event.messages;
    const withoutMarkers = messages !== event.messages ? { messages } : undefined;
    const current = run;
    const session = ctx.sessionManager.getSessionId();
    const request = current?.explicit;
    const latestUser = event.messages.findLastIndex(message => message.role === "user"
      || (message.role === "custom" && message.attribution === "user" && message.display));
    if (pending?.session === session && pending.settled && !pending.accepted && pending !== request) {
      const history = ctx.sessionManager.getBranch();
      const anchor = pending.leaf ? history.findIndex(entry => entry.id === pending?.leaf) : -1;
      if (history.slice(anchor + 1).some(entry => entry.type === "message" && authoredText(entry.message) === pending?.prompt)) {
        refuse(pending, ctx, REQUEST_CHANGED);
        pending = undefined;
        return withoutMarkers;
      }
    }
    if (!current || current.session !== session || current.agent !== ctx.agent.id) return withoutMarkers;
    const marker = event.messages.findLastIndex(message => isMarker(message) && message.role === "custom"
      && (message.details as { id?: unknown } | undefined)?.id === current.id);
    const text = latestUser >= 0 ? authoredText(event.messages[latestUser]) : undefined;
    const latest = event.messages[latestUser];

    if (request) {
      if (text !== request.prompt || (latest.role === "user" && latest.steering)
        || (!request.accepted && (pending !== request || marker <= latestUser))) {
        refuse(request, ctx, REQUEST_CHANGED);
        return withoutMarkers;
      }
      if ((request.source && answerPosition(event.messages, request.source, { backward: (current.sourcePosition ?? 0) < 0, end: latestUser }) !== current.sourcePosition)
        || (request.interpretation && answerPosition(event.messages, request.interpretation, { backward: (current.interpretationPosition ?? 0) < 0, end: latestUser }) !== current.interpretationPosition)) {
        refuse(request, ctx, "The selected handoff changed during preparation. Paste the handoff or retry /elivibe.");
        return withoutMarkers;
      }
      request.accepted = true;
    } else {
      if (text === undefined || marker <= latestUser || letsReplyStand(text)) return withoutMarkers;
      const leaf = ctx.sessionManager.getBranch();
      const anchor = current.baseline ? leaf.findIndex(entry => entry.id === current.baseline) : -1;
      if (current.baseline && anchor < 0) return withoutMarkers;
      const users = leaf.slice(anchor + 1).filter(entry => entry.type === "message" && entry.message.role === "user");
      if (users.length > 1) return withoutMarkers;
      if (latest.role === "user" && latest.steering) return withoutMarkers;
    }

    if (!current.applied) {
      current.applied = true;
      try {
        pi.appendEntry(APPLIED, current.id);
      } catch {
        // Teaching still works if the host cannot persist follow-up identity.
      }
    }
    return withoutMarkers;
  });

  // OMP's pre-execution veto is turn-local. It does not remove provider tool schemas
  // or change the active roster (including other extensions' policy).
  pi.on("tool_call", (_event, ctx) => {
    if (run?.explicit && run.session === ctx.sessionManager.getSessionId() && run.agent === ctx.agent.id) {
      return { block: true, reason: "eliVibe explanation turns do not run tools." };
    }
  });

  function save(change: Partial<Config>, ctx: ExtensionContext) {
    const next = { ...preference(ctx), ...change };
    try {
      pi.appendEntry(SETTINGS, next);
    } catch {
      ctx.ui.notify("eliVibe could not save preferences; settings were not changed.", "warning");
      return;
    }
    ctx.ui.notify(`eliVibe: ${next.mode} mode, ${next.depth} depth.`, "info");
  }

  pi.registerCommand("elivibe", {
    description: "Explain a technical handoff, ask a follow-up, or adjust eliVibe",
    getArgumentCompletions(prefix) {
      return argumentCompletions(prefix).map(value => ({ value, label: value }));
    },
    async handler(args, ctx) {
      const command = parseCommand(args);
      const notify = (text: string) => ctx.ui.notify(text, "info");
      switch (command.kind) {
        case "help":
          notify(HELP);
          return;
        case "invalid":
          notify("Invalid eliVibe option. Use /elivibe help, or /elivibe explain <text> for a question beginning with a command word.");
          return;
        case "retired":
          notify("eliVibe model, judge, and consent controls were retired. Saved routes and grants are ignored. Use OMP’s /model to select the conversation model.");
          return;
        case "status": {
          const { mode, depth } = preference(ctx);
          const next = !ctx.models.current() ? NO_MODEL : !ctx.isIdle() || ctx.hasPendingMessages() ? BUSY
            : "Using the active OMP model. Try /elivibe with a specific question or after a technical handoff.";
          notify(`eliVibe: ${mode} mode, ${depth} depth. ${next}`);
          return;
        }
        case "set":
          save(command.change, ctx);
          return;
        case "settings": {
          const label = "Use /elivibe off|manual|light|full or /elivibe depth auto|brief|detailed.";
          if (!ctx.hasUI || ctx.mode !== "tui" || typeof ctx.ui.select !== "function") {
            notify(label);
            return;
          }
          const { mode, depth } = preference(ctx);
          const session = ctx.sessionManager.getSessionId();
          const leaf = ctx.sessionManager.getLeafId();
          let selected: string | undefined;
          try {
            selected = await ctx.ui.select(`eliVibe: ${mode} mode, ${depth} depth`, [
              ...MODES.map(value => `mode ${value}`), ...DEPTHS.map(value => `depth ${value}`),
            ]);
          } catch {
            notify(label);
            return;
          }
          if (!selected || session !== ctx.sessionManager.getSessionId() || leaf !== ctx.sessionManager.getLeafId()) return;
          const choice = parseCommand(selected);
          if (choice.kind === "set") save(choice.change, ctx);
          return;
        }
      }

      const session = ctx.sessionManager.getSessionId();
      if ((pending?.session === session && !pending.settled) || !ctx.isIdle() || ctx.hasPendingMessages()) {
        notify(BUSY);
        return;
      }
      const { source: handoff, lesson, retained } = history(ctx.sessionManager.getBranch());
      const source = command.kind === "more" ? lesson?.source : handoff;
      const interpretation = lesson?.interpretation;
      if (command.kind === "explain" && (!source || !retained(source))) {
        notify(NO_SOURCE);
        return;
      }
      if (command.kind === "more" && (!source || !interpretation || !retained(interpretation) || !retained(source))) {
        notify(NO_EXPLANATION);
        return;
      }
      if (!ctx.models.current()) {
        notify(NO_MODEL);
        return;
      }
      // sendUserMessage skips slash expansion, but OMP still expands @path and ^model mentions.
      if (/(?:^|[\s([{<"'`])@[^\s@]|(?:^|\s)\^[^\s^]+(?=\s|$)/.test(args)) {
        notify("Paste the relevant text instead of using @file or ^model mentions in an explanation request.");
        return;
      }
      const request: Pending = {
        session, leaf: ctx.sessionManager.getLeafId(), prompt: args ? `/elivibe ${args}` : "/elivibe",
        intent: command.kind, source: retained(source) ? source : undefined,
        interpretation: command.kind === "more" ? interpretation : undefined, accepted: false, settled: false,
      };
      pending = request;
      try {
        // Only the actual slash request is user-authored; policy is added by the host hook.
        await pi.sendUserMessage(request.prompt, { attribution: "user" });
      } catch {
        if (pending === request && request.session === ctx.sessionManager.getSessionId() && !request.accepted && !request.refused) {
          notify("OMP could not start the explanation. Check its model with /model, or retry /elivibe.");
        }
      } finally {
        request.settled = true;
        if (pending === request && (request.accepted || (ctx.isIdle() && !ctx.hasPendingMessages()))) pending = undefined;
        if (run?.explicit === request) run = undefined;
      }
    },
  });
}
