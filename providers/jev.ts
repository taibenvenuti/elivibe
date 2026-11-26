export const JEV_ENDPOINT = 'https://api.typesafe.ai/v1/systemone';

type Decision = 'skip' | 'brief' | 'detailed';

type JevRequest = { model: string; report: string; instructions: string; signal: AbortSignal };

function jsonObject(value: unknown): Record<string, unknown> | undefined {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
    ? value as Record<string, unknown> : undefined;
}

export async function requestJev(
  { model, report, instructions, signal }: JevRequest,
  apiKey: string,
  send: (url: string, options: RequestInit) => Promise<Response> = fetch,
): Promise<Decision> {
  if (apiKey === 'N/A' || !/^[A-Za-z0-9._~+/-]+=*$/.test(apiKey)) throw new Error('Missing or invalid TypeSafe authorization');
  signal.throwIfAborted();
  const response = await send(JEV_ENDPOINT, {
    method: 'POST', redirect: 'error', credentials: 'omit', signal,
    headers: { Authorization: `Bearer ${apiKey}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model, state: report,
      questions: { handoff: { type: 'choice', instructions, criteria: { skip: null, brief: null, detailed: null } } },
    }),
  });
  if (!response.ok) throw new Error(`TypeSafe request failed (${response.status})`);
  const body = jsonObject(await response.json().catch(() => undefined));
  const answer = jsonObject(jsonObject(body?.answers)?.handoff);
  if (answer?.type === 'choice') {
    const { choice } = answer;
    if (choice === 'skip' || choice === 'brief' || choice === 'detailed') return choice;
  }
  throw new Error('Invalid TypeSafe choice');
}
