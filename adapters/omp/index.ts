import { readFileSync } from "node:fs";
import type { ExtensionAPI, ExtensionContext } from "@oh-my-pi/pi-coding-agent";
import {
  effectiveExplanationModel,
  ModelContextLimitError,
  ModelOutputLimitError,
  fullInstructions,
  parseConfig,
  processReport,
  type Config,
  type ModelBinding,
} from "../../core/index.ts";
import { JEV_ENDPOINT, requestJev } from "../../providers/jev.ts";

const CUSTOM_TYPE = "elivibe-handoff";
const SETTINGS_TYPE = "elivibe-settings";
const JEV_ORIGIN = new URL(JEV_ENDPOINT).origin;
// OMP 19.2.1 ModelRegistry.getApiKey returns this for auth: none.
const NO_AUTH = "N/A";
const ISOLATED_NOTICE = "Isolated requests do not include conversation history or run OMP’s Hide Secrets and provider hooks. Only approve handoff text you can share; provider charges may apply.";
const MODES = ["manual", "light", "full", "off"] as const;
const DEPTHS = ["adaptive", "brief", "detailed"] as const;
const USAGE = "/elivibe [status | manual | light | full | off | depth adaptive|brief|detailed | model [auto|<provider>/<id>] | judge <provider>/<id> | consent <provider>/<id> [confirm] | judge-consent <provider>/<id> [confirm] | consent off | judge-consent off]";

function bindingName(binding: ModelBinding | undefined): string {
  return binding ? `${binding.provider}/${binding.model}` : "not set";
}

function parseBinding(selector: string | undefined): ModelBinding | undefined {
  const match = /^([^/\s\p{C}]{1,256})\/([^\s\p{C}]{1,256})$/u.exec(selector ?? "");
  return match ? { provider: match[1], model: match[2] } : undefined;
}

function exactModel(ctx: ExtensionContext, binding: ModelBinding) {
  const model = ctx.modelRegistry.find(binding.provider, binding.model);
  return model?.provider === binding.provider && model.id === binding.model ? model : undefined;
}

function modelBinding(model: Model | undefined): ModelBinding | undefined {
  return model && { provider: model.provider, model: model.id };
}

function sameBinding(left: ModelBinding | undefined, right: ModelBinding | undefined): boolean {
  return !!left && left.provider === right?.provider && left.model === right.model;
}

function isJev(binding: ModelBinding): boolean {
  return binding.provider === "typesafe" && /^jev-[\w.-]+$/.test(binding.model);
}

type Model = NonNullable<ExtensionContext["model"]>;
type Destination = { binding: ModelBinding; api: "openai-completions" | "typesafe"; endpoint: string };

function destination(model: Model | undefined): Destination | undefined {
  if (!model || model.transport === "pi-native") return;
  const { provider, id, api, baseUrl } = model;
  const binding = { provider, model: id };
  if (isJev(binding)) {
    if (api === "typesafe" && [JEV_ORIGIN, `${JEV_ORIGIN}/`].includes(baseUrl)) {
      return { binding, api: "typesafe", endpoint: JEV_ENDPOINT };
    }
    return;
  }
  if (api !== "openai-completions" || (model.requestModelId && model.requestModelId !== id)) return;
  const url = URL.parse(baseUrl);
  // Reject ambiguous spellings before URL normalization can turn them into a different authority or path.
  if (!url || !/^https?:\/\/[^/?#]+(?:\/[^?#]*)?$/.test(baseUrl) || /[\\%\s\p{C}]/u.test(baseUrl)
    || url.username || url.password || url.pathname.includes("//")
    || (baseUrl !== url.href && `${baseUrl}/` !== url.href)
    || (url.protocol !== "https:" && !["127.0.0.1", "[::1]"].includes(url.hostname))) return;
  return { binding, api: "openai-completions", endpoint: `${url.href.replace(/\/$/, "")}/chat/completions` };
}

function sameDestination(left: Destination | undefined, right: Destination | undefined): boolean {
  return !!left && !!right && sameBinding(left.binding, right.binding) && left.api === right.api
    && left.endpoint === right.endpoint;
}

function selectedRoute(ctx: ExtensionContext, binding: ModelBinding, useActive: boolean): Destination | undefined {
  const registered = destination(exactModel(ctx, binding));
  return !useActive || sameDestination(registered, destination(ctx.models.current())) ? registered : undefined;
}

function supportedModel(model: Model, judgment: boolean): boolean {
  return model.transport !== "pi-native"
    && (model.api === "openai-completions" || (judgment && model.api === "typesafe" && isJev(modelBinding(model)!)));
}

function destinationName(route: Destination): string {
  return `${route.endpoint} (${route.api})`;
}

class RequestRestriction extends Error {}

const ROUTE_CHANGED = "The selected destination changed or is unavailable. Check `/elivibe status` and reapprove the exact destination, or use `/skill:elivibe` in the native conversation.";
const UNSUPPORTED_ROUTE = "This OMP transport is not supported for isolated requests. Use full mode for future handoffs or `/skill:elivibe` in the native conversation.";

type ProxyBypass = (endpoint: URL) => boolean;

function checkNetwork(route: Destination, bypassesProxy: ProxyBypass | undefined): void {
  const env = process.env;
  const https = route.endpoint.startsWith("https://");
  // Match OMP 19.2.1's provider key. Don't attempt to reproduce its proxy bypass rules.
  const providerProxy = `PI_PROXY_${route.binding.provider.toUpperCase().replace(/[^A-Z0-9]/g, "_")}`;
  if (env[providerProxy] || env.PI_PROXY || env.ALL_PROXY || env.all_proxy
    || (https ? env.HTTPS_PROXY || env.https_proxy : env.HTTP_PROXY || env.http_proxy)) {
    throw new RequestRestriction("Isolated requests cannot honor the process proxy configured for this destination. Use full mode for future handoffs or `/skill:elivibe` in the native conversation.");
  }
  if (https && env.NODE_TLS_REJECT_UNAUTHORIZED === "0") {
    throw new RequestRestriction("Isolated HTTPS requires certificate verification. Restore TLS verification or use `/skill:elivibe`.");
  }
  // Reading OMP's provider cache seeds it on a miss. Its startup PI_PROXY wrapper has no getter.
  // A host bypass applies to both, without reading or changing either retained value.
  try {
    if (bypassesProxy?.(new URL(route.endpoint)) === true) return;
  } catch {
    // Resolver errors can contain network configuration; never include them in a notice.
  }
  throw new RequestRestriction("eliVibe cannot establish direct transport under OMP's effective proxy policy. Use full mode for future handoffs or `/skill:elivibe` in the native conversation.");
}

function jsonObject(value: unknown): Record<string, unknown> | undefined {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? value as Record<string, unknown> : undefined;
}

async function requestChat(
  route: Destination, apiKey: string, options: { instructions: string; input: string; maxTokens: number; signal: AbortSignal },
  send: typeof fetch,
): Promise<string> {
  const { instructions, input, maxTokens, signal } = options;
  // Call the verified wire protocol directly. OMP's stream dispatcher can substitute native or provider-specific transports.
  const response = await send(route.endpoint, {
    method: "POST", redirect: "error", credentials: "omit", signal,
    headers: { "Content-Type": "application/json", ...(apiKey === NO_AUTH ? {} : { Authorization: `Bearer ${apiKey}` }) },
    body: JSON.stringify({
      model: route.binding.model, stream: false, max_tokens: maxTokens,
      messages: [{ role: "system", content: instructions }, { role: "user", content: input }],
    }),
  });
  if (!response.ok) {
    if (response.status === 400) {
      const body = jsonObject(await response.json().catch(() => undefined));
      if (jsonObject(body?.error)?.code === "context_length_exceeded") throw new ModelContextLimitError();
    }
    throw new Error("Isolated chat request failed");
  }
  const choices = jsonObject(await response.json())?.choices;
  const choice = Array.isArray(choices) && choices.length === 1 ? jsonObject(choices[0]) : undefined;
  if (choice?.finish_reason === "length") throw new ModelOutputLimitError();
  const message = jsonObject(choice?.message);
  if (choice?.finish_reason === "stop" && message?.role === "assistant" && typeof message.content === "string"
    && message.function_call == null && (message.tool_calls == null
      || (Array.isArray(message.tool_calls) && message.tool_calls.length === 0))) {
    return message.content;
  }
  throw new Error("Incomplete isolated chat response");
}

type SessionEntry = ReturnType<ExtensionContext["sessionManager"]["getBranch"]>[number];
type SessionMessage = Extract<SessionEntry, { type: "message" }>["message"];

function stoppedText(message: SessionMessage | undefined): string | undefined {
  if (message?.role !== "assistant" || message.stopReason !== "stop") return;
  let text = "";
  for (const part of message.content) {
    if (part.type === "toolCall") return;
    if (part.type === "text") text += text ? `\n\n${part.text}` : part.text;
  }
  return text.trim() || undefined;
}

interface Handoff {
  id: string;
  text: string;
  timestamp: number;
  supplemented: boolean;
}

function previousHandoff(ctx: ExtensionContext): Handoff | undefined {
  const branch = ctx.sessionManager.getBranch();
  for (let i = branch.length - 1; i >= 0; i--) {
    const entry = branch[i];
    if (entry.type !== "message") continue;
    if (entry.message.role !== "assistant") return;
    const text = stoppedText(entry.message);
    if (!text) return;
    let supplemented = false;
    for (let j = i + 1; j < branch.length; j++) {
      const later = branch[j];
      const details = later.type === "custom_message" && later.customType === CUSTOM_TYPE
        ? later.details as { sourceId?: unknown } | undefined : undefined;
      if (details?.sourceId === entry.id) {
        supplemented = true;
        break;
      }
    }
    return { id: entry.id, text, timestamp: entry.message.timestamp, supplemented };
  }
}

function explicitSkill(prompt: string): boolean {
  return /\/skill:elivibe(?![\w/.-])|<skill name="elivibe" location="[^"\r\n]+">\r?\n/i.test(prompt);
}

function leavesReplyUnchanged(prompt: string): boolean {
  return explicitSkill(prompt) || /\b(?:no elivibe|without elivibe|skip elivibe|elivibe off|do not (?:use|run) elivibe|don't (?:use|run) elivibe)\b/i.test(prompt)
    || /\b(?:reply|respond|answer|output|return|give|provide|format)\b[^\n.!?]{0,60}\b(?:only|(?:as|in) (?:a )?(?:json|yaml|csv|xml|markdown|plain text|table|diff|patch|code))\b/i.test(prompt);
}


export default async function elivibe(pi: ExtensionAPI): Promise<void> {
  // This host-only subpath may be unavailable; Full mode must still register.
  const proxy = await import("@oh-my-pi/pi-ai/utils/proxy").catch(() => undefined);
  registerElivibe(pi, proxy?.shouldBypassProxy);
}

export function registerElivibe(pi: ExtensionAPI, bypassesProxy: ProxyBypass | undefined): void {
  const methodology = readFileSync(new URL("../../skill/elivibe/SKILL.md", import.meta.url), "utf8")
    .replace(/^---\r?\n[\s\S]*?\r?\n---[ \t]*\r?\n/, "").trim();
  let config = parseConfig(undefined);
  let sessionId: string | undefined;
  let registry: ExtensionContext["modelRegistry"] | undefined;
  let current: { baseline: string | null } | undefined;
  let pending: AbortController | undefined;
  let lastDelivered: string | undefined;
  let skipInput = false;
  let rewriteRoute: Destination | undefined;
  let judgeRoute: Destination | undefined;
  let reviews: Partial<Record<"consent" | "judgeConsent", Destination>> = {};

  function invalidate(): void {
    current = undefined;
    pending?.abort();
    pending = undefined;
  }

  function leaveSession(): void {
    reviews = {};
    invalidate();
  }

  function reset(ctx: ExtensionContext): void {
    leaveSession();
    lastDelivered = undefined;
    skipInput = false;
    rewriteRoute = undefined;
    judgeRoute = undefined;
    registry = ctx.modelRegistry;
    sessionId = ctx.sessionManager.getSessionId();
    const settings = ctx.sessionManager.getBranch().findLast(entry => entry.type === "custom" && entry.customType === SETTINGS_TYPE);
    const { mode, depth, model, judgeModel } = parseConfig(settings?.type === "custom" ? settings.data : undefined);
    config = { mode, depth, model, judgeModel };
  }

  function syncSession(ctx: ExtensionContext): void {
    if (sessionId !== ctx.sessionManager.getSessionId()) reset(ctx);
  }

  async function supplement(ctx: ExtensionContext, handoff: Handoff, trigger: "automatic" | "manual"): Promise<void> {
    const alreadySupplemented = handoff.supplemented || handoff.id === lastDelivered;
    if (alreadySupplemented || pending) {
      if (trigger === "manual") ctx.ui.notify(alreadySupplemented ? "eliVibe already supplemented this handoff." : "eliVibe is already processing a handoff.", "info");
      return;
    }
    const request = new AbortController();
    pending = request;
    const owner = sessionId;
    const selected = config;
    const expectedRewriteRoute = rewriteRoute;
    const expectedJudgeRoute = judgeRoute;
    const followActive = !selected.model;
    // OMP copies ctx.model into command contexts; the model query remains live.
    const liveModel = followActive ? modelBinding(ctx.models.current()) : undefined;
    const explanationModel = effectiveExplanationModel(selected, liveModel);
    let restriction: string | undefined;
    try {
      const currentHandoff = () => {
        if (request.signal.aborted || pending !== request || sessionId !== owner || ctx.sessionManager.getSessionId() !== owner
          || !ctx.isIdle() || ctx.hasPendingMessages()) return false;
        const latest = previousHandoff(ctx);
        return latest?.id === handoff.id && latest.text === handoff.text && !latest.supplemented;
      };
      const checkRoute = (binding: ModelBinding, route: Destination | undefined, useActive: boolean): Destination => {
        if (!route || !sameDestination(selectedRoute(ctx, binding, useActive), route)) {
          if (route && rewriteRoute === route) rewriteRoute = undefined;
          if (route && judgeRoute === route) judgeRoute = undefined;
          throw new RequestRestriction(ROUTE_CHANGED);
        }
        return route;
      };
      const checkExplanationRoute = () => {
        if (!explanationModel) throw new RequestRestriction(ROUTE_CHANGED);
        return checkRoute(explanationModel, expectedRewriteRoute, followActive);
      };
      const result = await processReport({
        config: selected,
        trigger,
        report: handoff.text,
        activeModel: liveModel,
        methodology,
        signal: request.signal,
        model: async ({ kind, binding, instructions, input, maxOutputTokens, signal }) => {
          const isJudge = kind === "judge";
          const checkDispatch = () => {
            signal.throwIfAborted();
            if (!currentHandoff()) {
              request.abort();
              signal.throwIfAborted();
            }
            const explanation = checkExplanationRoute();
            // Revalidate the judgment grant even after it has returned a decision.
            const judgment = trigger === "automatic" && selected.judgeModel
              ? checkRoute(selected.judgeModel, expectedJudgeRoute, false) : undefined;
            checkNetwork(explanation, bypassesProxy);
            if (judgment) checkNetwork(judgment, bypassesProxy);
            if (!isJudge) return explanation;
            if (!judgment) throw new RequestRestriction(ROUTE_CHANGED);
            return judgment;
          };
          try {
            const route = checkDispatch();
            const model = exactModel(ctx, binding);
            if (!model || !sameDestination(destination(model), route)) throw new RequestRestriction(ROUTE_CHANGED);
            checkNetwork(route, bypassesProxy);
            const apiKey = await ctx.modelRegistry.getApiKey(model, owner, { signal });
            checkDispatch();
            if (!apiKey) throw new RequestRestriction("The selected model is not authenticated. Sign in with OMP or choose an authenticated model.");
            if ((apiKey !== NO_AUTH && (!/^[A-Za-z0-9._~+/-]+=*$/.test(apiKey) || !route.endpoint.startsWith("https://")))
              || (route.api === "typesafe" && apiKey === NO_AUTH)) {
              throw new RequestRestriction("This isolated route requires a plain bearer credential over HTTPS, or keyless chat authentication. Use an eligible model or `/skill:elivibe`.");
            }
            const send: typeof fetch = (url, options) => {
              checkDispatch();
              return fetch(url, options);
            };
            if (route.api === "typesafe" && isJudge) return await requestJev({ model: binding.model, instructions, report: input, signal }, apiKey, send);
            const maxTokens = Math.min(maxOutputTokens, model.maxTokens ?? maxOutputTokens);
            if (!Number.isSafeInteger(maxTokens) || maxTokens < 1) throw new RequestRestriction("The selected model has no usable output budget.");
            return await requestChat(route, apiKey, { instructions, input, maxTokens, signal }, send);
          } catch (error) {
            if (error instanceof RequestRestriction) restriction = error.message;
            throw error;
          }
        },
      });
      if (!currentHandoff()) return;
      if (result.status !== "explained") {
        if (trigger === "manual" || result.status === "failed") {
          const remedies: Record<string, string> = {
            "explanation-consent-required": explanationModel
              ? `No approved explanation destination for ${bindingName(explanationModel)}. Run \`/elivibe consent ${bindingName(explanationModel)}\` to review and follow the confirmation instructions, or use \`/skill:elivibe\` in the native conversation.`
              : "OMP has no active explanation model. Select an eligible model or use `/skill:elivibe`.",
            "judgment-consent-required": `No approved judging destination for ${bindingName(selected.judgeModel)}. Run \`/elivibe judge-consent ${bindingName(selected.judgeModel)}\` to review and follow the confirmation instructions, or use manual mode.`,
            privacy: "This isolated route blocks recognizable sensitive material, transcripts, and source excerpts. Ask for a clean handoff or use `/skill:elivibe` in the native conversation.",
            "context-limit": "The model could not fit the whole handoff, instructions and response. Choose and approve a larger-context model, or ask for a shorter handoff.",
            "output-limit": result.status === "failed" && result.stage === "judgment"
              ? "The judging response hit its output limit. Use `/elivibe` to explain the handoff manually."
              : "The explanation hit the model’s output limit. Try brief depth or select and approve a model with more room.",
            "judgment-budget": "The judging request would exceed the 8 KiB UTF-8 limit, including instructions. Use `/elivibe` to explain the handoff manually instead.",
            timeout: "The request timed out. Retry or choose another approved model.",
            "not-needed": "No explanation was needed.",
            identical: "The model repeated the handoff rather than explaining it. Retry or choose another approved model.",
          };
          const stage = result.status === "failed" ? ` ${result.stage}` : "";
          ctx.ui.notify(`eliVibe kept the original: ${restriction ?? remedies[result.reason] ?? `The${stage} request did not produce a usable result. Check OMP model availability or choose another approved model.`}`, "info");
        }
        return;
      }
      try {
        checkExplanationRoute();
        if (trigger === "automatic" && selected.judgeModel) checkRoute(selected.judgeModel, expectedJudgeRoute, false);
      } catch {
        return;
      }
      const judge = trigger === "automatic" ? `; judged by ${bindingName(selected.judgeModel)}` : "";
      pi.sendMessage({
        customType: CUSTOM_TYPE,
        content: `eliVibe (${bindingName(explanationModel)}; supplementary${judge}; original above)\n\n${result.text}`,
        details: { sourceId: handoff.id },
        display: true,
        excludeFromContext: true,
      }, { triggerTurn: false });
      lastDelivered = handoff.id;
    } finally {
      if (pending === request) pending = undefined;
    }
  }

  pi.on("session_start", (_event, ctx) => reset(ctx));
  pi.on("session_switch", (_event, ctx) => reset(ctx));
  pi.on("session_clear", (_event, ctx) => reset(ctx));
  pi.on("session_branch", (_event, ctx) => reset(ctx));
  pi.on("session_tree", (_event, ctx) => reset(ctx));
  pi.on("session_before_switch", leaveSession);
  pi.on("session_before_branch", leaveSession);
  pi.on("session_before_tree", leaveSession);
  pi.on("session_before_shutdown", leaveSession);
  pi.on("session_shutdown", () => {
    leaveSession();
    rewriteRoute = undefined;
    judgeRoute = undefined;
    registry = undefined;
    config = parseConfig(undefined);
    sessionId = undefined;
  });

  pi.on("input", event => {
    if (config.mode === "off" || event.source === "extension" || /^\/elivibe(?:\s|$)/.test(event.text)) return;
    invalidate();
    skipInput = leavesReplyUnchanged(event.text);
  });
  pi.on("before_agent_start", (event, ctx) => {
    syncSession(ctx);
    if (event.reason !== "prompt") return;
    invalidate();
    const inputOptOut = skipInput;
    skipInput = false;
    if (config.mode === "off") return;
    const skip = inputOptOut || leavesReplyUnchanged(event.prompt);
    if (skip) return;
    if (config.mode === "light") current = { baseline: ctx.sessionManager.getLeafId() };
    const instructions = fullInstructions(config, methodology);
    if (instructions) {
      return { systemPrompt: [...event.systemPrompt, `${instructions}\n\nFor this turn eliVibe’s methodology is already included above. Do not read or invoke the standalone eliVibe skill again.`] };
    }
  });
  pi.on("agent_start", () => pending?.abort());
  pi.on("session_before_compact", () => pending?.abort());
  pi.on("agent_end", (event, ctx) => {
    const owner = sessionId;
    if (event.willContinue || ctx.sessionManager.getSessionId() !== owner) return;
    const run = current;
    current = undefined;
    if (!run || !ctx.isIdle() || ctx.hasPendingMessages()) return;
    const last = event.messages.at(-1);
    const handoff = previousHandoff(ctx);
    if (!handoff || handoff.id === run.baseline || handoff.timestamp !== last?.timestamp || handoff.text !== stoppedText(last)) return;
    if (config.mode !== "light") return;
    // OMP serializes delivery per extension. Returning lets a before-switch event abort this work.
    void supplement(ctx, handoff, "automatic").catch(() => {
      if (sessionId === owner && ctx.sessionManager.getSessionId() === owner && previousHandoff(ctx)?.id === handoff.id) {
        ctx.ui.notify("eliVibe kept the original: the isolated request could not be completed.", "info");
      }
    });
  });

  pi.registerCommand("elivibe", {
    description: "Supplement the preceding handoff or configure eliVibe",
    getArgumentCompletions(prefix) {
      const match = /^(model|judge)\s+(\S*)$/.exec(prefix.trimStart());
      if (!match) return null;
      const [, command, query] = match;
      const matches = command === "model" && "auto".startsWith(query)
        ? [{ value: "model auto", label: "auto", description: "Use OMP’s active model" }] : [];
      for (const model of registry?.getAll() ?? []) {
        if (!supportedModel(model, command === "judge")) continue;
        const canonical = `${model.provider}/${model.id}`;
        if ((canonical.startsWith(query) || model.id.startsWith(query)) && destination(model)) {
          matches.push({ value: `${command} ${canonical}`, label: canonical, description: model.name });
        }
      }
      return matches;
    },
    async handler(args, ctx) {
      syncSession(ctx);
      const [command, value, ...extra] = args.trim().split(/\s+/);
      if (!command) {
        if (config.mode === "off" || config.mode === "full") {
          ctx.ui.notify(`eliVibe ${config.mode} mode does not make supplementary requests. Use \`/elivibe manual\` to enable them.`, "info");
          return;
        }
        if (!ctx.isIdle() || ctx.hasPendingMessages()) {
          ctx.ui.notify("Wait for OMP to finish before requesting an eliVibe handoff.", "info");
          return;
        }
        const handoff = previousHandoff(ctx);
        if (!handoff) {
          ctx.ui.notify("There is no preceding completed assistant handoff to supplement. Wait for a complete response or ask OMP for a handoff first.", "info");
          return;
        }
        await supplement(ctx, handoff, "manual");
        return;
      }
      const effective = config.model ?? modelBinding(ctx.models.current());
      if ((command === "model" || command === "status") && !value) {
        const selected = effective && selectedRoute(ctx, effective, !config.model);
        const explanation = selected?.api === "openai-completions" ? selected : undefined;
        const selection = config.model ? `override ${bindingName(config.model)}` : "auto";
        const explanationLabel = !effective ? "none (no active model)"
          : explanation ? `${bindingName(effective)} at ${destinationName(explanation)}`
            : `unavailable (${bindingName(effective)})`;
        const modelLabel = `${selection}; effective ${explanationLabel}`;
        if (command === "model") {
          ctx.ui.notify(`eliVibe explanation model: ${modelLabel}.`, "info");
          return;
        }
        const judge = config.judgeModel;
        const judgment = judge && selectedRoute(ctx, judge, false);
        const judgmentLabel = judgment ? `${bindingName(judge)} at ${destinationName(judgment)}`
          : judge ? `unavailable (${bindingName(judge)})` : bindingName(judge);
        const explanationApproval = !rewriteRoute ? "not approved"
          : sameDestination(explanation, rewriteRoute) ? "approved for this session" : "destination changed; reapprove";
        const judgmentApproval = !judgeRoute ? "not approved"
          : sameDestination(judgment, judgeRoute) ? "approved for this session" : "destination changed; reapprove";
        ctx.ui.notify(`eliVibe: ${config.mode} (${config.depth ?? "adaptive"}) • explanation ${modelLabel} (${explanationApproval}) • judgment ${judgmentLabel} (${judgmentApproval}). ${ISOLATED_NOTICE}`, "info");
        return;
      }
      const mode = MODES.find(item => item === (command === "mode" ? value : !value ? command : undefined));
      const depth = command === "depth" ? DEPTHS.find(item => item === value) : undefined;
      const modelCommand = command === "model" || command === "judge";
      const auto = command === "model" && value === "auto";
      let binding = parseBinding(value);
      if (modelCommand && value && !auto && !value.includes("/")) {
        const candidates = ctx.modelRegistry.getAll().filter(model => model.id === value);
        if (candidates.length > 1) {
          ctx.ui.notify("This model ID is ambiguous. Choose an exact installed provider/model.", "warning");
          return;
        }
        binding = modelBinding(candidates[0]);
      }
      const consentCommand = command === "consent" || command === "judge-consent";
      const confirm = consentCommand && !!binding && extra.length === 1 && extra[0] === "confirm";
      if ((extra.length && !confirm) || (!mode && !depth && !(modelCommand && value) && !(consentCommand && (binding || value === "off")))) {
        ctx.ui.notify(USAGE, "warning");
        return;
      }
      const judgment = command === "judge" || command === "judge-consent";
      const consentKey = judgment ? "judgeConsent" : "consent";
      const reviewed = consentCommand ? reviews[consentKey] : undefined;
      if (consentCommand) delete reviews[consentKey];
      const model = binding && exactModel(ctx, binding);
      if ((modelCommand && !auto && !binding) || (binding && !model)) {
        ctx.ui.notify("Choose an exact installed provider/model for this role; no fallback is used.", "warning");
        return;
      }
      if (model && !supportedModel(model, judgment)) {
        ctx.ui.notify(binding && isJev(binding) && !judgment
          ? "TypeSafe Jev is only supported for judgment. Choose another explanation model." : UNSUPPORTED_ROUTE, "warning");
        return;
      }
      const route = destination(model);
      if (binding && model && !route) {
        ctx.ui.notify(isJev(binding) ? `TypeSafe Jev can only be approved for ${JEV_ENDPOINT}. The installed model uses a different route.`
          : "The installed model has no verifiable isolated route. Use HTTPS or literal loopback HTTP with an unambiguous base URL and no credentials, query, or fragment, or use `/skill:elivibe`.", "warning");
        return;
      }
      let next = config;
      if (consentCommand) {
        const configured = judgment ? config.judgeModel : effective;
        if (binding && !sameBinding(binding, configured)) {
          ctx.ui.notify("Approval applies only to the exact effective provider/model. Check `/elivibe status` or select this model first.", "warning");
          return;
        }
        if (binding && !judgment && !config.model && !sameDestination(route, selectedRoute(ctx, binding, true))) {
          ctx.ui.notify(ROUTE_CHANGED, "warning");
          return;
        }
        if (route) {
          if (ctx.mode !== "rpc" && !(ctx.mode === "tui" && ctx.hasUI)) {
            ctx.ui.notify("eliVibe route approval requires a user command in the interactive terminal or an RPC client that displays notices.", "warning");
            return;
          }
          const role = judgment ? "judgment" : "explanation";
          const reviewCommand = `/elivibe ${command} ${bindingName(route.binding)}`;
          if (!confirm) {
            ctx.ui.notify(`Review eliVibe ${role} route: ${bindingName(route.binding)} at ${destinationName(route)}. eliVibe can send preceding handoff text to this destination. ${ISOLATED_NOTICE} If you approve this exact route, run \`${reviewCommand} confirm\`.`, "info");
            reviews[consentKey] = route;
            return;
          }
          if (!sameDestination(reviewed, route)) {
            ctx.ui.notify(`No matching eliVibe ${role} route review. Run \`${reviewCommand}\` for fresh review before confirming.`, "warning");
            return;
          }
        }
        next = { ...config, [consentKey]: binding };
      } else {
        next = mode ? { ...config, mode } : depth ? { ...config, depth } : judgment
          ? { ...config, judgeModel: binding, judgeConsent: undefined }
          : { ...config, model: binding, consent: undefined };
        try {
          const { mode, depth, model, judgeModel } = next;
          pi.appendEntry(SETTINGS_TYPE, { mode, depth, model, judgeModel });
        } catch {
          ctx.ui.notify("eliVibe could not save preferences in this OMP session; settings were not changed.", "warning");
          return;
        }
      }
      invalidate();
      config = next;
      if (consentCommand || modelCommand) {
        delete reviews[consentKey];
        if (judgment) judgeRoute = consentCommand ? route : undefined;
        else rewriteRoute = consentCommand ? route : undefined;
      }
      if (consentCommand && route) {
        ctx.ui.notify(`Approved ${bindingName(route.binding)} for ${judgment ? "judgment" : "explanation"} in this session. eliVibe can send the preceding handoff text to ${destinationName(route)}. ${ISOLATED_NOTICE}`, "info");
      } else if (modelCommand && route) {
        ctx.ui.notify(`Selected ${bindingName(route.binding)} at ${destinationName(route)}. To review this route for approval, use \`/elivibe ${judgment ? "judge-consent" : "consent"} ${bindingName(route.binding)}\`. ${ISOLATED_NOTICE}`, "info");
      } else {
        ctx.ui.notify(consentCommand ? "eliVibe approval revoked." : "eliVibe settings saved for this session. See /elivibe status.", "info");
      }
    },
  });
}
