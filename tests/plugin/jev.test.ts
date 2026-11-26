import assert from 'node:assert/strict';
import test from 'node:test';
import { requestJev } from '../../providers/jev.ts';

const request = { model: 'jev-1.14.0', report: 'The fix is staged, not deployed.', instructions: 'Select the needed depth.', signal: new AbortController().signal };

test('Jev sends one typed question about the report, not a chat session', async () => {
  const choice = await requestJev(request, 'synthetic', async (url, options) => {
    assert.equal(url, 'https://api.typesafe.ai/v1/systemone');
    assert.equal(options.redirect, 'error');
    assert.equal(options.credentials, 'omit');
    assert.equal(options.signal, request.signal);
    assert.equal(new Headers(options.headers).get('authorization'), 'Bearer synthetic');
    const body = JSON.parse(String(options.body));
    assert.deepEqual(body, { model: request.model, state: request.report, questions: { handoff: {
      type: 'choice', instructions: request.instructions, criteria: { skip: null, brief: null, detailed: null },
    } } });
    return Response.json({ answers: { handoff: { type: 'choice', choice: 'brief' } } });
  });
  assert.equal(choice, 'brief');
});

test('Jev rejects malformed decisions and does not retry or echo provider errors', async () => {
  await assert.rejects(requestJev(request, 'synthetic', async () => new Response('private invalid body')), {
    message: 'Invalid TypeSafe choice',
  });
  for (const value of [{ type: 'choice', choice: 'yes' }, { type: 'score', choice: 'brief' }]) {
    await assert.rejects(requestJev(request, 'synthetic', async () => Response.json({ answers: { handoff: value } })), /Invalid TypeSafe choice/);
  }
  let calls = 0;
  await assert.rejects(requestJev(request, 'synthetic', async () => {
    calls++;
    return new Response('sensitive error details', { status: 429 });
  }), { message: 'TypeSafe request failed (429)' });
  assert.equal(calls, 1);
});

test('Jev does not dispatch with a keyless or non-bearer credential', async () => {
  for (const key of ['', 'N/A', 'key\nkey', '{"token":"synthetic"}']) {
    await assert.rejects(requestJev(request, key, async () => assert.fail('No authorized request')), {
      message: 'Missing or invalid TypeSafe authorization',
    });
  }
});
