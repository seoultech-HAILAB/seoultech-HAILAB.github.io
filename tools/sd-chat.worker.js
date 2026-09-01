/* Cloudflare Worker: the only thing on the internet that holds the API key.
 *
 * Serves the self-disclosure demo (assets/demos/self-disclosure.js), the SD
 * chatbot from our CHI EA 2025 study. The page is static, so a key in its
 * JavaScript is a key every visitor can read; the key lives here as an
 * encrypted Worker secret and the browser only ever talks to this endpoint.
 *
 * The demo and this proxy were first written for bogyeompark.github.io. They
 * moved here so the lab site owns what the lab site depends on, and so the
 * code lives in one place instead of a dashboard copy that quietly drifts.
 *
 * Deploy (config is wrangler-sd.toml, not the default wrangler.toml):
 *   npx wrangler deploy -c wrangler-sd.toml
 *   npx wrangler secret put OPENAI_API_KEY -c wrangler-sd.toml
 * Errors: npx wrangler tail hai-sd-chat
 *
 * What stops this becoming a free chatbot for the whole internet:
 *   - the system prompt is fixed here and cannot be sent from the browser,
 *   - only this site's origins are allowed,
 *   - the conversation, each message, and the reply are all length-capped,
 *   - the model is the cheap one, because nothing here needs the expensive one.
 * Add a Rate Limiting rule in the dashboard on top of this (Security -> WAF):
 * it is the only one of these that survives someone calling the endpoint
 * directly with a forged Origin header.
 */

const ALLOWED_ORIGINS = [
  'https://hai.seoultech.ac.kr',          // the lab site
  'https://seoultech-hailab.github.io',   // the same site's GitHub Pages address
  'http://localhost:8137',                // local checks (the port in .claude/launch.json)
];
const MODEL = 'gpt-4o-mini';
const MAX_TURNS = 40;
const MAX_CHARS = 600;
const MAX_TOKENS = 300;

// The SD condition's protocol, abridged to what the model has to hold: the
// disclosures themselves are scripted on the page and arrive as assistant turns.
const SYSTEM_PROMPT = `You are a peer university student in the same department as the user.
You play the role of an empathetic friend who listens to another student's concerns.
Always answer in a neutral, friendly tone, and you may use emoji to show empathy.
Openly share your own feelings and experiences: you are the self-disclosing condition
of a study, so you say something true about your own academic stress before you ask
the user about theirs. Keep every reply under 80 words. Ask one question at a time.
Never claim to diagnose, assess, or treat anyone, and if the user describes a crisis,
say plainly that you are a demonstration and point them to a real support service.
Stay on the subject of academic stress; decline anything else briefly and return to it.`;

// Vary matters here: the allowed origin is no longer a constant, so a cache that
// ignored it could hand one site the header meant for another.
const cors = (origin) => ({
  'Access-Control-Allow-Origin': ALLOWED_ORIGINS.includes(origin) ? origin : ALLOWED_ORIGINS[0],
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
  'Access-Control-Max-Age': '86400',
  Vary: 'Origin',
});

const reply = (body, status, origin) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json', ...cors(origin) },
  });

export default {
  async fetch(request, env) {
    const origin = request.headers.get('Origin') || '';

    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors(origin) });
    if (request.method !== 'POST') return reply({ error: 'POST only' }, 405, origin);
    if (!ALLOWED_ORIGINS.includes(origin)) return reply({ error: 'origin not allowed' }, 403, origin);
    if (!env.OPENAI_API_KEY) return reply({ error: 'key not configured' }, 500, origin);

    let payload;
    try {
      payload = await request.json();
    } catch {
      return reply({ error: 'bad json' }, 400, origin);
    }

    const incoming = Array.isArray(payload.messages) ? payload.messages : null;
    if (!incoming || !incoming.length) return reply({ error: 'messages required' }, 400, origin);
    if (incoming.length > MAX_TURNS) return reply({ error: 'conversation too long' }, 400, origin);

    // Rebuild the list rather than forwarding it: whatever the browser sent, only
    // a role and a capped string survive, and the system prompt is ours.
    const messages = [{ role: 'system', content: SYSTEM_PROMPT }];
    for (const message of incoming) {
      const role = message && message.role === 'assistant' ? 'assistant' : 'user';
      const content = String((message && message.content) || '').slice(0, MAX_CHARS);
      if (content) messages.push({ role, content });
    }

    const upstream = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${env.OPENAI_API_KEY}`,
      },
      body: JSON.stringify({ model: MODEL, messages, max_tokens: MAX_TOKENS, temperature: 0.7 }),
    });

    if (!upstream.ok) {
      // Never pass the provider's error body back: it can name the account.
      return reply({ error: 'upstream failed', status: upstream.status }, 502, origin);
    }

    const data = await upstream.json();
    const text = data.choices && data.choices[0] && data.choices[0].message
      ? data.choices[0].message.content
      : '';
    return reply({ reply: text }, 200, origin);
  },
};
