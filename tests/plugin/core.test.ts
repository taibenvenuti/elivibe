import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { type Config, DEFAULT_JUDGE_MODEL, ModelContextLimitError, type ModelOperation, ModelOutputLimitError, fullInstructions, parseConfig, processReport } from "../../core/index.ts";

const methodology = readFileSync(new URL("../../skill/elivibe/SKILL.md", import.meta.url), "utf8");
const report = "Migrated existing records. The dry run passed; the production migration has not run.";
const explanation = "A dry run checks the proposed changes without writing them. It cannot prove that production will accept the writes or that the records have actually changed.";
const explanationModel = { provider: "chat", model: "explainer" };
const judgeModel = { provider: "judge", model: "classifier" };
const config = {
	mode: "light",
	depth: "adaptive",
	model: explanationModel,
	consent: explanationModel,
	judgeModel,
	judgeConsent: judgeModel,
} satisfies Config;
const defaults = { config, report, methodology, trigger: "automatic" } as const;

function transport(...responses: (string | Error)[]) {
	const calls: Parameters<ModelOperation>[0][] = [];
	const model: ModelOperation = async (request) => {
		const response = responses[calls.length];
		calls.push(request);
		if (response instanceof Error) throw response;
		assert.ok(response !== undefined, "unexpected model call");
		return response;
	};
	return { model, calls };
}

test("unrecognized settings are manual and don't coerce model identifiers or consent", () => {
	const fallback = parseConfig(undefined);
	assert.equal(fallback.mode, "manual");
	assert.equal(fallback.depth, "adaptive");
	assert.deepEqual(fallback.judgeModel, { provider: "typesafe", model: "jev-1.14.0" });
	assert.equal(fallback.judgeConsent, undefined);
	const parsed = parseConfig({ mode: "LIGHT", model: { provider: " chat", model: "explainer" }, consent: "chat/explainer" });
	assert.equal(parsed.mode, "manual");
	assert.equal(parsed.model, undefined);
	assert.equal(parsed.consent, undefined);
	assert.equal(parseConfig({ depth: "unexpected" }).depth, "adaptive");
	assert.equal(parseConfig(parseConfig({ judgeModel: "bad" })).judgeModel, undefined);
	assert.deepEqual(parseConfig(config), config);
});

test("off, native full and unrequested manual make no auxiliary calls", async () => {
	const { model, calls } = transport();
	for (const mode of ["off", "full", "manual"] as const) {
		const settings = { ...config, mode };
		const instructions = fullInstructions(settings, methodology);
		if (mode === "full") {
			assert.ok(instructions?.startsWith(methodology));
		} else {
			assert.equal(instructions, undefined);
		}
		for (const trigger of mode === "manual" ? ["automatic"] as const : ["automatic", "manual"] as const) {
			assert.deepEqual(await processReport({ ...defaults, trigger, config: settings, model }), { status: "unchanged", reason: "mode" });
		}
	}
	const brief = fullInstructions({ mode: "full", depth: "brief" }, methodology);
	const detailed = fullInstructions({ mode: "full", depth: "detailed" }, methodology);
	assert.ok(brief?.startsWith(methodology) && detailed?.startsWith(methodology));
	assert.notEqual(brief, methodology);
	assert.notEqual(detailed, methodology);
	assert.notEqual(brief, detailed);
	assert.equal(calls.length, 0);
});

test("manual uses the proven active route by default and makes one teaching request", async () => {
	const { model, calls } = transport(explanation, explanation);
	const task = "Migrate production records without downtime.";
	const settings: Config = { mode: "manual" };
	assert.deepEqual(await processReport({ ...defaults, trigger: "manual", config: settings, activeRoute: explanationModel, task, model }),
		{ status: "explained", text: explanation, depth: "adaptive" });
	assert.deepEqual(await processReport({ ...defaults, trigger: "manual", config: { ...settings, model: explanationModel }, activeRoute: explanationModel, model }),
		{ status: "explained", text: explanation, depth: "adaptive" });
	assert.deepEqual(calls.map(({ kind, binding }) => [kind, binding]), [["explain", explanationModel], ["explain", explanationModel]]);
	assert.equal(calls[0].input, JSON.stringify({ handoff: report, task }));
	assert.equal(calls[1].input, report);
	assert.ok(calls[0].instructions.startsWith(methodology));
});

test("manual cross-route consent is exact and light always needs both explicit consents", async () => {
	const { model, calls } = transport(explanation);
	const activeRoute = { ...explanationModel, model: "another-explainer" };
	const task = "This context must not go to another route.";
	const manual = { ...defaults, trigger: "manual", activeRoute, task, model } as const;
	assert.deepEqual(await processReport({ ...manual, config: { ...config, consent: activeRoute } }),
		{ status: "unchanged", reason: "explanation-consent-required" });
	assert.deepEqual(await processReport({ ...manual, config: { ...config, mode: "manual" } }),
		{ status: "explained", text: explanation, depth: "adaptive" });
	assert.equal(calls[0].input, report);

	assert.deepEqual(await processReport({ ...defaults, config: { ...config, consent: activeRoute }, activeRoute: explanationModel, model }),
		{ status: "unchanged", reason: "explanation-consent-required" });
	for (const judgeConsent of [undefined, { ...judgeModel, provider: "a-different-provider" }]) {
		assert.deepEqual(await processReport({ ...defaults, config: { ...config, judgeConsent }, model }),
			{ status: "unchanged", reason: "judgment-consent-required" });
	}
	assert.equal(calls.length, 1);
});

test("auto in light follows the current model, not its previous approval or the judge", async () => {
	const { model, calls } = transport("brief", explanation);
	const settings = { ...config, model: undefined };
	const current = { provider: "another-provider", model: explanationModel.model };
	assert.deepEqual(await processReport({ ...defaults, config: settings, activeModel: current, model }),
		{ status: "unchanged", reason: "explanation-consent-required" });
	assert.equal(calls.length, 0);
	const approved = { ...settings, consent: current };
	assert.equal((await processReport({ ...defaults, config: approved, activeModel: current, model })).status, "explained");
	assert.deepEqual(calls.map(call => call.binding), [judgeModel, current]);
});

test("selecting the active model is not permission to use an unverified destination", async () => {
	const { model, calls } = transport();
	const current = { provider: "new-provider", model: explanationModel.model };
	for (const selected of [undefined, explanationModel]) {
		const result = await processReport({ ...defaults, trigger: "manual", config: { mode: "manual", model: selected },
			activeModel: current, activeRoute: explanationModel, model });
		assert.deepEqual(result, { status: "unchanged", reason: "explanation-consent-required" });
	}
	assert.equal(calls.length, 0);
});

test("light skips when there is no knowledge gap and spends only one judgment call", async () => {
	const settings = { ...config, depth: "detailed" } satisfies Config;
	const { model, calls } = transport("skip\n");
	assert.deepEqual(await processReport({ ...defaults, config: settings, model }), { status: "unchanged", reason: "not-needed" });
	assert.equal(calls.length, 1);
	assert.equal(calls[0].kind, "judge");
	assert.deepEqual(calls[0].binding, judgeModel);
});

test("light can teach from a well-written report and shares only the handoff", async () => {
	for (const depth of ["brief", "detailed"] as const) {
		const { model, calls } = transport(depth, explanation);
		assert.deepEqual(await processReport({ ...defaults, model, task: "Do not share this task.", activeRoute: explanationModel }),
			{ status: "explained", text: explanation, depth });
		assert.deepEqual(calls.map(({ kind, binding }) => [kind, binding]), [["judge", judgeModel], ["explain", explanationModel]]);
		assert.deepEqual(calls.map(({ input }) => input), [report, report]);
		assert.equal(calls[0].signal, calls[1].signal);
		assert.equal(calls[0].maxOutputTokens, 16);
		assert.equal(calls[1].maxOutputTokens, depth === "brief" ? 350 : 900);
		assert.ok(calls[1].instructions.startsWith(methodology));
	}
});

test("explicit depth applies to both explanation modes without reducing a complex report's budget", async () => {
	const manual = transport(explanation);
	const light = transport("detailed", explanation);
	const settings = { ...config, depth: "brief" } satisfies Config;
	assert.deepEqual(await processReport({ ...defaults, config: settings, trigger: "manual", model: manual.model }),
		{ status: "explained", text: explanation, depth: "brief" });
	assert.deepEqual(await processReport({ ...defaults, config: settings, model: light.model }),
		{ status: "explained", text: explanation, depth: "brief" });
	assert.equal(light.calls[1].maxOutputTokens, 900);
	assert.equal(light.calls[1].instructions, manual.calls[0].instructions);
});

test("the default judge still needs its own consent", async () => {
	const { model, calls } = transport("skip");
	const settings: Config = { mode: "light", model: explanationModel, consent: explanationModel };
	assert.deepEqual(await processReport({ ...defaults, config: settings, model }),
		{ status: "unchanged", reason: "judgment-consent-required" });
	assert.equal(calls.length, 0);
	assert.deepEqual(await processReport({ ...defaults, config: { ...settings, judgeConsent: DEFAULT_JUDGE_MODEL }, model }),
		{ status: "unchanged", reason: "not-needed" });
	assert.deepEqual(calls[0].binding, DEFAULT_JUDGE_MODEL);
});

test("alternative judgment reuses the same screened input and central criteria", async () => {
	const { model, calls } = transport(explanation);
	const chat = transport("skip");
	await processReport({ ...defaults, model: chat.model });
	const result = await processReport({ ...defaults, model, judge: async ({ input, binding, instructions }) => {
		assert.equal(input, report);
		assert.deepEqual(binding, judgeModel);
		assert.equal(instructions, chat.calls[0].instructions);
		return "detailed";
	} });
	assert.equal(result.status, "explained");
	assert.deepEqual(calls.map(({ kind }) => kind), ["explain"]);
});

test("unnecessary or unsafe payloads are kept local", async () => {
	const { model, calls } = transport();
	for (const [input, reason] of [
		["\n\t", "empty"],
		["Authorization: Bearer example-not-an-actual-credential", "privacy"],
		["API_KEY=`synthetic-fixture`", "privacy"],
		["Rotate at https://example:fake@example.com/path", "privacy"],
		["-----BEGIN PRIVATE KEY-----", "privacy"],
		["Tool output: copied raw content", "privacy"],
		['{"role": "assistant", "content": "copied transcript"}', "privacy"],
		["const internalSetting = 42;", "privacy"],
		["Changed code:\n```ts\nconst x = 1;\n```", "privacy"],
	]) {
		assert.deepEqual(await processReport({ ...defaults, model, report: input }), { status: "unchanged", reason });
	}
	assert.equal(calls.length, 0);
});

test("same-route manual accepts benign snippets and omits unsafe or oversized optional task input", async () => {
	const handoff = "The option is read once at startup:\n```ts\nconst cacheEnabled = true;\n```";
	const illustration = "Changing the configuration file does not change the value the running process already read:\n```text\nedit file → process still uses old value\nrestart → process reads new value\n```";
	const { model, calls } = transport(illustration, illustration);
	const manual = { ...defaults, config: { mode: "manual" }, trigger: "manual", activeRoute: explanationModel, model } as const;
	for (const task of ["API_KEY=synthetic-fixture", "x".repeat(513)]) {
		assert.deepEqual(await processReport({ ...manual, report: handoff, task }),
			{ status: "explained", text: illustration, depth: "adaptive" });
	}
	assert.deepEqual(calls.map(({ input }) => input), [handoff, handoff]);
	for (const raw of ["Tool output: copied raw content", "password: synthetic-fixture"]) {
		assert.deepEqual(await processReport({ ...manual, report: `${handoff}\n${raw}` }), { status: "unchanged", reason: "privacy" });
	}
	assert.equal(calls.length, 2);
});

test("long explanation inputs reach the model whole without an artificial limit", async () => {
	const longReport = `${"Production records depend on the current schema. ".repeat(500)}Production writes have not run.`;
	const { model, calls } = transport(explanation);
	const manual = { ...defaults, trigger: "manual", report: longReport, model } as const;
	assert.deepEqual(await processReport(manual), { status: "explained", text: explanation, depth: "adaptive" });
	assert.equal(calls[0].input, longReport);
	assert.deepEqual(await processReport({ ...manual, trigger: "automatic" }),
		{ status: "failed", stage: "judgment", reason: "judgment-budget" });
	assert.equal(calls.length, 1);
});

test("counted budgets are independent and account for instructions and output reserve", async () => {
	const longReport = `Dry-run log summary: ${"unchanged row ".repeat(700)}; no writes.`;
	const { model, calls } = transport("brief", explanation);
	const measureTokens: NonNullable<Parameters<typeof processReport>[0]["measureTokens"]> = ({ kind, input, instructions }) => {
		assert.equal(input, longReport);
		assert.ok(instructions.length > 0);
		return kind === "judge" ? { inputTokens: 4080, contextWindow: 16384 } : { inputTokens: 4850, contextWindow: 5200 };
	};
	const measured = { ...defaults, report: longReport, model, measureTokens };
	assert.deepEqual(await processReport(measured), { status: "explained", text: explanation, depth: "brief" });
	assert.equal(calls.length, 2);
	assert.deepEqual(await processReport({ ...measured, measureTokens: () => ({ inputTokens: 4081, contextWindow: 16384 }) }),
		{ status: "failed", stage: "judgment", reason: "judgment-budget" });
	assert.deepEqual(await processReport({ ...measured, trigger: "manual", measureTokens: () => ({ inputTokens: 5200, contextWindow: 5200 }) }),
		{ status: "failed", stage: "explanation", reason: "context-limit" });
	assert.equal(calls.length, 2);
});

test("exact counts omit optional context and reserve the output that fits without truncating the handoff", async () => {
	const { model, calls } = transport(explanation);
	const result = await processReport({
		...defaults, config: { mode: "manual" }, trigger: "manual", activeRoute: explanationModel,
		task: "Migrate production without downtime.", model,
		measureTokens: ({ input }) => ({ inputTokens: input === report ? 1500 : 1564, contextWindow: 1564 }),
	});
	assert.deepEqual(result, { status: "explained", text: explanation, depth: "adaptive" });
	assert.equal(calls.length, 1);
	assert.equal(calls[0].input, report);
	assert.equal(calls[0].maxOutputTokens, 64);
});

test("failures identify the inference stage without exposing provider errors", async () => {
	for (const [responses, stage, reason] of [
		[["probably brief"], "judgment", "invalid-judgment"],
		[[new Error("a request could contain private details")], "judgment", "model-error"],
		[[new ModelContextLimitError("private provider response")], "judgment", "context-limit"],
		[["brief", new Error("a response could contain private details")], "explanation", "model-error"],
		[["brief", new ModelContextLimitError("private provider response")], "explanation", "context-limit"],
		[["brief", new ModelOutputLimitError("private provider response")], "explanation", "output-limit"],
		[["brief", "é".repeat(32 * 1024 + 1)], "explanation", "output-limit"],
		[["brief", "  "], "explanation", "invalid-explanation"],
		[["brief", "password: synthetic-fixture"], "explanation", "invalid-explanation"],
	] as const) {
		const { model, calls } = transport(...responses);
		assert.deepEqual(await processReport({ ...defaults, model }), { status: "failed", stage, reason });
		assert.equal(calls.length, responses.length);
	}
	const { model } = transport("brief", `  ${report}  `);
	assert.deepEqual(await processReport({ ...defaults, model }), { status: "unchanged", reason: "identical" });
});

test("a deadline aborts even an uncooperative judge and prevents a later explanation", async () => {
	const pending = Promise.withResolvers<string>();
	const calls: Parameters<ModelOperation>[0][] = [];
	const result = await processReport({ ...defaults, timeoutMs: 10, model: (request) => {
		calls.push(request);
		return pending.promise;
	} });
	assert.deepEqual(result, { status: "failed", stage: "judgment", reason: "timeout" });
	assert.equal(calls[0].signal.aborted, true);
	pending.resolve("detailed");
	await Promise.resolve();
	assert.deepEqual(calls.map(({ kind }) => kind), ["judge"]);
});

test("host cancellation returns promptly and discards an in-flight explanation", async () => {
	const pending = Promise.withResolvers<string>();
	const controller = new AbortController();
	const calls: Parameters<ModelOperation>[0][] = [];
	const result = processReport({ ...defaults, trigger: "manual", signal: controller.signal, model: (request) => {
		calls.push(request);
		return pending.promise;
	} });
	controller.abort();
	assert.deepEqual(await result, { status: "failed", stage: "explanation", reason: "cancelled" });
	assert.equal(calls[0].signal.aborted, true);
	pending.resolve(explanation);
});
