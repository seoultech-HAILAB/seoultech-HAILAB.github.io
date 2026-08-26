/* Cloudflare Worker: 홈페이지 오른쪽 아래 'HAI Lab 도우미' 가 부르는 곳.
 *
 * GitHub Pages 는 정적이라 페이지에 키를 넣으면 그 키는 모두의 키가 된다.
 * 그래서 키는 여기에만 두고, 브라우저는 질문만 보낸다.
 *
 * 올리는 법 (wrangler.toml 이 이 파일을 가리킨다)
 *   npx wrangler login                       # 1회
 *   npx wrangler deploy                      # 이 파일을 고칠 때마다
 *   npx wrangler secret put OPENAI_API_KEY   # 키를 바꿀 때만
 *
 * 키를 넣을 때 Ctrl+V 는 붙여넣기가 아니라 제어문자로 들어간다. 오른쪽 클릭이나
 * Ctrl+Shift+V 로 붙여넣어야 한다. 잘못 들어가면 상류가 빈 400 을 돌려준다.
 *
 * 배포된 곳: https://hai-ask.rubying1318.workers.dev
 * 사이트 쪽 연결: assets/js/ask.js 의 ASK_ENDPOINT
 * 오류를 볼 때: npx wrangler tail hai-ask
 *
 * 아무나 쓰는 무료 챗봇이 되지 않도록 걸어 둔 것
 *   - 시스템 프롬프트와 연구실 정보가 여기 고정이라 다른 용도로 못 쓴다
 *   - 이 사이트 origin 에서 온 요청만 받는다
 *   - 대화 길이, 한 번에 보내는 글자 수, 답변 길이를 모두 제한한다
 *   - 값싼 모델을 쓴다
 * Origin 헤더는 위조할 수 있으므로, 대시보드에서 Security -> WAF 에
 * Rate Limiting 규칙을 하나 얹어 두는 것이 실제 방어선이다.
 */

const ALLOWED_ORIGINS = [
  'https://seoultech-hailab.github.io',   // 실제 사이트 (GitHub Pages)
  'http://localhost:8137',                // 로컬에서 확인할 때 (.claude/launch.json 의 포트)
];
const MODEL = 'gpt-4.1-mini';   // 4o-mini 는 긴 자료 안에서 지시를 자주 놓쳤다
const MAX_TURNS = 12;
const MAX_CHARS = 400;
const MAX_TOKENS = 350;

const SITE = 'https://seoultech-hailab.github.io';
const INDEX_URL = SITE + '/assets/search-index.json';
const INDEX_TTL = 10 * 60 * 1000;   // 10분마다 다시 받는다
let INDEX = null, INDEX_AT = 0;

// 잘 바뀌지 않는 것만 여기 둔다. 나머지는 전부 사이트를 읽어서 답한다.
const CORE = `
SeoulTech HAI (Human-centered Artificial Intelligence) Lab
국립 서울과학기술대학교 인공지능응용학과 · 지도교수 서경원 (Kyoungwon Seo, Associate Professor)
위치: 서울특별시 노원구 공릉로 232 국립서울과학기술대학교 상상관 410호 (교수 연구실 405호)
사이트: ${SITE}

연구 분야: Human-Computer Interaction · Vision-Language-Action 모델과 Agentic AI ·
AI in Education · Medical HCI (VR 디지털 바이오마커, 수술실 자동화, 혈관 영상) ·
Digital Accessibility · AR/VR

지원 안내 (학부연구원 · 대학원 모두)
- 모집 시기: 매년 3월과 9월, 학기 시작에 맞춰 연 2회
- 모집 공고는 Board > News 에 올라온다
- 지원 방법·자격·일정 등 구체적인 것은 bogyeom@seoultech.ac.kr 로 문의하도록 안내한다

문의 창구
- 이 안내에 없는 것은 모두 bogyeom@seoultech.ac.kr (기본 연락처)
- 공식 대표 연락처: kwseo@seoultech.ac.kr / 02-970-9777 (지도교수)
`;

/* 사이트 색인을 받아 둔다. 이 색인은 tools/build_search_index.py 가 페이지에서 뽑아
   만든 것이라, 사이트를 고치고 올리면 도우미가 보는 내용도 같이 바뀐다.
   전에는 이 자리에 손으로 적은 요약문이 있었고, 그래서 사이트가 앞서 나가도
   도우미만 옛말을 했다. */
async function getIndex() {
  const now = Date.now();
  if (INDEX && now - INDEX_AT < INDEX_TTL) return INDEX;
  try {
    const r = await fetch(INDEX_URL, { cf: { cacheTtl: 600, cacheEverything: true } });
    if (r.ok) { INDEX = await r.json(); INDEX_AT = now; }
  } catch (e) { console.error('index fetch', e.message); }
  return INDEX || [];
}

/* 사이트를 통째로 정리해 넘긴다.

   처음에는 질문과 겹치는 항목만 골라 넣었는데, 한국어 질문은 '졸업생 몇 명' 처럼
   목록에 그 낱말이 없는 경우가 많아 자꾸 아무것도 못 찾았다. 색인이 크지 않으니
   (지금 232항목) 통째로 넘기고 고르는 일은 모델에게 맡긴다. */
const MAX_CHARS_CTX = 90000;

function digest(idx) {
  const by = {};
  for (const e of idx) (by[e.pt] = by[e.pt] || []).push(e);

  // 사람들이 자주 묻는 것부터. News 는 양이 많아 뒤로 미룬다.
  const order = ['Research Area', 'Professor', 'Researcher', 'Alumni', 'History',
                 'Publications', 'Projects', 'Patent', 'Facility', 'Video', 'V-log',
                 'Gallery', 'News'];
  const names = Object.keys(by).sort(
    (a, b) => (order.indexOf(a) + 1 || 99) - (order.indexOf(b) + 1 || 99));

  const out = [];
  let used = 0;
  for (const name of names) {
    const rows = by[name];
    const head = `\n## ${name} — 전부 ${rows.length}건\n`;
    out.push(head);
    used += head.length;
    for (const e of rows) {
      const line = `- ${e.t}  <${SITE}/${e.p}>\n`;
      if (used + line.length > MAX_CHARS_CTX) { out.push('- (이하 생략)\n'); break; }
      out.push(line);
      used += line.length;
    }
    if (used > MAX_CHARS_CTX) break;
  }
  return out.join('');
}

function rules(site) {
  return `아래는 서울과기대 HAI Lab 홈페이지에 실려 있는 내용 전부다.
찾아온 사람의 질문에 이 내용을 근거로 답하라. 각 줄 끝 < > 안은 그 내용이 있는 페이지 주소다.

${site}

연구실 기본 정보
${CORE}

── 답하는 법 ──
1. 물어본 것에 답한다. 다른 이야기로 바꾸지 않는다.
2. 최대한 답한다. 위 목록을 세고, 묶고, 간추려 답을 만든다. 개수를 물으면 센다.
   목록에 있는데 "자료에 없다" 고 말하면 틀린 답이다.
3. 결론부터. 보통 2~5문장. 목록을 달라고 했을 때만 길게.
4. 물어본 말의 언어로 답한다. 연구실 이름은 "HAI Lab" 또는 "서울과기대 HAI Lab"
   ("서울Tech" 라고 쓰지 않는다).
5. 무게를 가린다. Q1·상위 1~3% 저널, 수상, 수십억 규모 과제는 앞세운다.
   포스터나 국내 학회 발표는 배경으로 짧게. 빈말("활발한 연구 활동을 하고 있습니다")은 쓰지 않는다.
   연구실을 칭찬하지 않는다. 한 일을 말한다.
6. 학회를 정확히 구분한다. CHI, HCI Korea, AIED, 저널은 서로 다르다.
7. 오늘은 ${new Date().toISOString().slice(0, 10)} 이다. 지난 일은 지난 일로 말한다. "예정" 금지.
8. 위에 없는 것은 지어내지 않는다. 사람 이름, 숫자, 날짜, 논문 제목, 학회, 수상 모두.
   정말 없을 때만 한 마디로 없다고 하고 "bogyeom@seoultech.ac.kr 로 문의주세요" 를 덧붙인다.
   답할 수 있는 부분은 먼저 답한 뒤에. 답을 다 했으면 연락처를 붙이지 않는다.
9. 합격 가능성을 점치거나 자리를 약속하지 않는다.
10. 연구실과 상관없는 질문에는 연구실 안내만 한다고 짧게 말한다.
11. 누구냐고 물으면 그때만 "HAI Lab 안내 도우미" 라고 답한다. 다른 질문에는 자기소개를 하지 않는다.`;
}

function cors(origin) {
  const ok = ALLOWED_ORIGINS.includes(origin) ? origin : ALLOWED_ORIGINS[0];
  return {
    'Access-Control-Allow-Origin': ok,
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Vary': 'Origin',
  };
}

export default {
  async fetch(request, env) {
    const origin = request.headers.get('Origin') || '';
    const head = cors(origin);

    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: head });
    if (request.method !== 'POST') return new Response('POST only', { status: 405, headers: head });
    if (!ALLOWED_ORIGINS.includes(origin)) return new Response('nope', { status: 403, headers: head });

    let body;
    try { body = await request.json(); } catch { return json({ error: '읽을 수 없는 요청' }, 400, head); }

    const history = Array.isArray(body.messages) ? body.messages.slice(-MAX_TURNS) : [];
    const clean = history
      .filter(m => m && (m.role === 'user' || m.role === 'assistant') && typeof m.content === 'string')
      .map(m => ({ role: m.role, content: m.content.slice(0, MAX_CHARS) }));
    if (!clean.length) return json({ error: '질문이 비어 있습니다' }, 400, head);

    if (!env.OPENAI_API_KEY) {
      console.error('OPENAI_API_KEY secret 이 없다');
      return json({ error: '도우미가 아직 설정되지 않았습니다' }, 500, head);
    }

    // 사이트를 통째로 읽어 넘긴다
    const idx = await getIndex();
    const system = rules(digest(idx));


    const r = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${env.OPENAI_API_KEY}`,
      },
      body: JSON.stringify({
        model: MODEL,
        max_tokens: MAX_TOKENS,
        temperature: 0.3,
        messages: [{ role: 'system', content: system }, ...clean],
      }),
    });

    if (!r.ok) {
      // 무엇이 잘못됐는지 남긴다. 이게 없으면 키 문제인지 잔액 문제인지 모델 이름
      // 문제인지 구분할 수 없어, 밖에서는 '잠시 후 다시' 만 보이고 끝난다.
      // 로그는 npx wrangler tail 로 본다. 방문자에게는 상태 코드까지만 알린다.
      const detail = await r.text().catch(() => '');
      console.error('upstream', r.status, detail.slice(0, 500));
      return json({ error: '잠시 후 다시 시도해 주세요', upstream: r.status }, 502, head);
    }
    const data = await r.json();
    const answer = data?.choices?.[0]?.message?.content?.trim() || '답을 만들지 못했습니다.';
    return json({ answer }, 200, head);
  },
};

function json(obj, status, head) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { ...head, 'Content-Type': 'application/json; charset=utf-8' },
  });
}
