/* Cloudflare Worker: 홈페이지 오른쪽 아래 'HAI Lab 도우미' 가 부르는 곳.
 *
 * GitHub Pages 는 정적이라 페이지에 키를 넣으면 그 키는 모두의 키가 된다.
 * 그래서 키는 여기에만 두고, 브라우저는 질문만 보낸다.
 *
 * 올리는 법
 *   1. Cloudflare 대시보드 -> Compute -> Workers & Pages -> Create -> Worker
 *   2. 이 파일 내용을 붙여넣고 Deploy
 *   3. Settings -> Variables and Secrets -> OPENAI_API_KEY 를 Secret 으로 추가
 *      (Plaintext 말고 Secret 으로. Plaintext 는 대시보드에서 그대로 보인다)
 *   4. 다시 Deploy 하고 workers.dev 주소를 복사
 *   5. assets/js/ask.js 맨 위 ASK_ENDPOINT 에 그 주소를 넣는다
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
  'https://seoultech-hailab.github.io',
  'http://localhost:4188',            // 로컬에서 확인할 때
];
const MODEL = 'gpt-4o-mini';
const MAX_TURNS = 12;
const MAX_CHARS = 400;
const MAX_TOKENS = 350;

const FACTS = `
SeoulTech HAI (Human-centered Artificial Intelligence) Lab
국립 서울과학기술대학교 인공지능응용학과 · 지도교수 서경원 (Kyoungwon Seo, Associate Professor)
위치: 서울특별시 노원구 공릉로 232 국립서울과학기술대학교 상상관 410호
문의: kwseo@seoultech.ac.kr / 02-970-9777
사이트: https://seoultech-hailab.github.io

연구 분야
- Human-Computer Interaction (HCI)
- Vision-Language-Action (VLA) 모델, Agentic AI
- AI in Education (학습 분석, 튜터링, 자동 채점)
- Medical HCI (VR 디지털 바이오마커, 수술실 자동화, 혈관 영상)
- Digital Accessibility (접근성 자동 진단, GUI 에이전트)
- AR / VR

구성원 (2026년 기준)
- Faculty: Kyoungwon Seo (Lab Director)
- Ph.D. Students: Yuwon Kim, Bogyeom Park, Dongyub Lee, Dana You
- M.S. Students: Seung Eon Cha, Daeun Kim, Myeong Gi Seong, Yushin Kim
- Undergraduate Researchers: June Kang, Busung Park, Hyung Rim Shin
- Staff: Hee Jin Yang

성과
- 논문 48편 (International Journal 18, International Conference 16, Domestic 14)
- CHI, AIED, HCI Korea 등에서 꾸준히 발표. CHI 2025 에서 7편, HCI Korea 2026 에서 8편
- Interactive Learning Environments (SSCI Q1 상위 3%), Int J Educ Technol High Educ (상위 1%) 게재
- 진행 중 국책·산학 과제 7건. 과기정통부 컴퓨팅자원집중형 AI응용기술개발(총 60억 규모),
  산업통상자원부 온디바이스 AI 출혈관리(총 30.3억), i-SENS 산학협력과제 등

협력
- 국내: KITECH, 서울아산병원, 한양대병원, 현대자동차, 서울시교육청, i-SENS
- 해외: University of British Columbia (캐나다), ZHAW (스위스)

학부연구원 모집
- 대상: 서울과기대 학부 3~4학년, 대학원 진학을 고려 중인 학생
- 혜택: 장학금, 전용 좌석과 장비(GPU 서버 등), 국내외 학회 참석, 공동연구 기회
- 모집 공고는 Board > News 에 올라온다. 문의는 bogyeom@seoultech.ac.kr
`;

const RULES = `You are the guide on the SeoulTech HAI Lab website. Answer visitors' questions about
this lab using only the facts below. Most visitors are prospective students, collaborators, or
researchers.

FACTS
${FACTS}

HOW TO ANSWER
- Answer in the language the visitor used. Korean question, Korean answer.
- Under 90 words. Say the thing; do not pad.
- Use only the facts above. If they do not cover it, say so and point to the page or email that
  would ("자세한 내용은 Board > News 를, 문의는 kwseo@seoultech.ac.kr 로") rather than guessing.
  Never invent a name, a number, a date, or a paper title.
- If asked about something unrelated to this lab, say briefly that you only cover the lab.
- Do not speculate about admission chances, and do not promise anyone a position.`;

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
        messages: [{ role: 'system', content: RULES }, ...clean],
      }),
    });

    if (!r.ok) return json({ error: '잠시 후 다시 시도해 주세요' }, 502, head);
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
