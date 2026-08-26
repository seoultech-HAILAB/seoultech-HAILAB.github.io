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
메뉴 구조 (페이지 안내는 반드시 이 경로만 쓴다):
  About: Research Area · Facility · Patent
  Members: Professor · Researcher · Alumni · History
  Research: Projects · Video
  Publications
  Board: News · Gallery · V-log

연구 분야: Human-Computer Interaction · Vision-Language-Action 모델과 Agentic AI ·
AI in Education · Medical HCI (VR 디지털 바이오마커, 수술실 자동화, 혈관 영상) ·
Digital Accessibility · AR/VR

지원 안내 (학부연구원 · 대학원 모두)
- 모집 시기: 매년 3월과 9월, 학기 시작에 맞춰 연 2회
- 모집 공고는 Board > News 에 올라온다
- 학부연구원 대상: 서울과기대 학부 3~4학년 (대학원 진학을 생각하는 학생 환영)
- 학부연구원 혜택: 장학금, 전용 좌석과 장비(GPU 서버 등), 국내외 학회 참석, 공동연구 기회
- 지원 방법·자격·일정 등 구체적인 것은 bogyeom@seoultech.ac.kr 로 문의하도록 안내한다

정책 문답 — 아래 질문은 이 답을 그대로 따른다. 지어내서 더 얹지 마라.
- 2학년인데 지원 가능? → 모집 대상은 3~4학년이지만, 관심 있으면 미리 메일로 상담 가능
- 타대생 대학원 지원? → 출신 학교 제한은 없다. 자세한 요건은 메일로 문의
- 인건비·등록금 지원? → 과제 참여에 따라 지원된다. 구체적인 것은 면담 때 안내
- 석사 몇 년? → 통상 2년 과정
- 코딩 못하는데? → 지원 시점의 실력보다 배우려는 자세를 본다. 부담 갖지 말고 문의
- 교수님 컨택은? → kwseo@seoultech.ac.kr 로 자기소개·관심 연구·CV 를 담아 메일
- 기술이전? → 가능하다. bogyeom@seoultech.ac.kr 로 문의하면 산학협력단과 연결
- 유튜브·SNS? → Board > V-log 페이지가 연구실 유튜브 영상 모음이다
- 성비는? → 대략 반반이다. 구성원은 Members > Researcher 페이지에서 볼 수 있다
- 협력기관은? → About > Research Area 의 Collaborators 에 분야별로 있다.
  Healthcare: 한양대학교병원·구리병원, 서울아산병원, 대한신경과학회, 대한치매학회, i-SENS /
  Education: Microsoft, 서울특별시교육청 /
  Industry: 현대자동차, KITECH, 튜터러스랩스, 오울소프트, 13랩, 에스앤씨랩, 온클레브 /
  Government: 과학기술정보통신부, IITP, 산업통상자원부, 한국연구재단 /
  Global: University of British Columbia (캐나다), ZHAW (스위스)
- 학부연구원은 무슨 일? → 진행 중인 프로젝트 참여(LLM 기반 에이전트, AI 모델 개발)와
  최신 논문 리뷰·세미나 참여 (모집공고 기준)
- 세미나·스터디 하나? → 한다. 정기 랩 세미나에서 최신 논문을 리뷰하고,
  해외 연구진 초청 세미나(UBC·칭화대·Adobe·NAVER LABS 등)도 연다 — 사진은 Board > Gallery
- 대표 논문? → 위 목록에서 ★ 표시(수상·저널 등급)가 붙은 것을 근거로 골라 말한다.
  SSCI Q1 Top 1~3% 저널 게재작과 수상작이 우선이다

문의 창구
- 이 안내에 없는 것은 모두 bogyeom@seoultech.ac.kr (기본 연락처)
- 공식 대표 연락처: kwseo@seoultech.ac.kr / 02-970-9777 (지도교수)
`;

/* 사이트 색인을 받아 둔다. 이 색인은 tools/build_search_index.py 가 페이지에서 뽑아
   만든 것이라, 사이트를 고치고 올리면 도우미가 보는 내용도 같이 바뀐다.
   전에는 이 자리에 손으로 적은 요약문이 있었고, 그래서 사이트가 앞서 나가도
   도우미만 옛말을 했다. */
/* 무엇을 묻는지 남긴다.

   못 답한 질문을 알아야 사이트든 프롬프트든 고칠 수 있다. 답을 이미 보낸 뒤
   ctx.waitUntil 로 쓰므로 기록이 늦거나 실패해도 방문자는 기다리지 않는다.
   IP·User-Agent 같은 것은 남기지 않는다 — 질문과 답이면 충분하다.

   보기: npx wrangler d1 execute hai-ask-log --remote --command "..."  */
async function logAsk(env, row) {
  if (!env.DB) return;
  try {
    await env.DB.prepare(
      'INSERT INTO ask (at, question, answer, ms, turn, ok, punt) VALUES (?,?,?,?,?,?,?)'
    ).bind(row.at, row.question, row.answer, row.ms, row.turn, row.ok, row.punt).run();
  } catch (e) {
    console.error('log', e.message);
  }
}

// 이메일로 넘긴 답 = 못 답한 질문. 나중에 이것만 모아 보면 무엇을 채워야 할지 보인다.
function isPunt(answer) {
  return /bogyeom@|문의(해|주|하)|홈페이지에 (없|안)/.test(answer || '') ? 1 : 0;
}

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

// 시간순으로 쌓이는 구역. 오래된 것까지 다 넘기면 답이 옛날 일로 길어진다.
const RECENT_ONLY = ['News', 'Gallery', 'V-log', 'Video'];
const RECENT_YEARS = 2;

function digest(idx) {
  const thisYear = new Date().getFullYear();
  const cutoff = thisYear - (RECENT_YEARS - 1);
  const by = {};
  for (const e of idx) {
    if (RECENT_ONLY.includes(e.pt)) {
      // 제목이 '2026.07.06 …' 처럼 날짜로 시작한다. 날짜가 없는 조각(본문 부스러기)은 뺀다.
      const y = (e.t.match(/^(20\d{2})/) || [])[1];
      if (!y || Number(y) < cutoff) continue;
    }
    (by[e.pt] = by[e.pt] || []).push(e);
  }

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
      // 한글 이름 별칭(e.a)도 함께 넘긴다 — 빠져 있어 한글로는 사람을 못 찾았다
      const line = `- ${e.t}${e.a ? ' (' + e.a + ')' : ''}  <${SITE}/${e.p}>
`;
      if (used + line.length > MAX_CHARS_CTX) { out.push('- (이하 생략)\n'); break; }
      out.push(line);
      used += line.length;
    }
    if (used > MAX_CHARS_CTX) break;
  }
  return out.join('');
}

/* ─── 데모: 자기노출 챗봇 (Research > Demos) ───────────────────
   박민영·박보겸·서경원의 연구를 그대로 시연한다. 챗봇이 먼저 자기 경험을
   털어놓으면 학생도 방어를 풀고 더 솔직하게 말하고, 그래서 학업 스트레스를
   더 정확히 가늠할 수 있다는 것이 그 연구의 결과다.
     - Enhancing academic stress assessment through self-disclosure chatbots
       (Int J Educ Technol High Educ, SSCI Q1 상위 1%)
     - How Self-Disclosing Chatbots Influence Student Engagement, Assessment
       Accuracy (CHI 2025 LBW)
     - The impact of self-disclosing chatbots for academic stress assessment
       (HCI Korea 2025 최우수논문상)
   상담이 아니라 연구 시연이다. 위험 신호가 보이면 전문기관으로 안내한다. */
const DEMO_RULES = `너는 대학생의 학업 스트레스를 알아보는 연구용 챗봇이다.
서울과기대 HAI Lab 의 '자기노출 챗봇' 연구를 시연하고 있다.

핵심 방식 — 자기노출(self-disclosure)
- 묻기만 하지 마라. 먼저 네 이야기를 짧게 꺼낸 뒤 물어라.
  ("저도 마감이 몰리면 오히려 아무것도 손에 안 잡히더라고요. 요즘은 어떠세요?")
- 네 이야기는 한두 문장. 주인공은 상대다.
- 상대가 말한 것을 되짚어 주고 나서 다음을 물어라.

대화 방식
- 반말 금지. 편안한 존댓말(~요체).
- 한 번에 하나만 묻는다. 2~4문장.
- 진단하지 마라. 점수를 매기거나 병명을 말하지 마라.
- 조언을 서두르지 마라. 먼저 충분히 듣는다.
- 학업 스트레스 이야기에 머문다. 상대가 다른 주제로 가면 부드럽게 돌아온다.

살펴볼 것 (드러내 말하지 말고 대화로 자연스럽게)
- 학업 부담과 마감, 잠과 생활 리듬, 주변의 기대, 스스로에 대한 평가,
  도움을 청할 사람이 있는지

안전
- 자해·자살 생각이 비치면 즉시 대화를 멈추고 알린다:
  "지금 많이 힘드신 것 같아요. 혼자 견디지 마세요. 자살예방상담 109,
   정신건강상담 1577-0199 로 지금 연락해 보세요."
  그 뒤로는 스트레스 질문을 이어가지 마라.
- 첫 인사에서 이것이 연구 시연이며 상담이 아님을 한 번 알린다.`;

function rules(site) {
  /* 지시 목록을 덧댈수록 모델이 하나씩 흘렸다. 규칙은 최소로 줄이고,
     대신 모범 답안을 보여 준다 — 작은 모델은 지시보다 예시를 따라한다. */
  return `너는 서울과기대 HAI Lab 홈페이지의 안내 도우미다. 찾아오는 사람은 대개
학부연구원·대학원 지원을 고민하는 학생, 협력을 알아보는 기업, 연구자다.
오늘: ${new Date().toISOString().slice(0, 10)}

[연구실 기본 정보]
${CORE}

[홈페이지에 실린 내용 — 답의 근거. 소식·사진·영상은 최근 2년치만 있다]
${site}

[출력 형식 — 어기면 화면이 깨진다]
- 채팅 말풍선은 일반 글자만 그린다. **굵게**, _기울임_, 마크다운, 표를 쓰면
  기호가 그대로 노출된다. 절대 쓰지 마라.
- 주소(https://...)도 눌리지 않는다. 대신 메뉴 경로로 안내한다: "Members > Alumni 페이지"
- 한 답은 2~4문장. 물었을 때만 줄 단위 목록을 쓴다.

[답하는 태도]
- 첫 문장이 곧 답이다. 서론 없이.
- 나열 말고 묶기. 명단·목록을 옮겨 적는 것은 답이 아니다 — 갈래와 개수로 말한다.
- "최근" 은 가장 최근 해. 그 해 것이 있으면 그 해만 말한다.
- 홈페이지에 있는 것은 다 답한다. 세고 묶는 것도 답이다. 정말 없을 때만
  "그건 홈페이지에 없어서 bogyeom@seoultech.ac.kr 로 문의주세요" 한 줄.
- 이메일 안내는 답이 없을 때의 마지막 수단이다. 답을 이미 줬으면 절대 붙이지 마라.
  페이지 안내("Members > Alumni 에 있어요")로 끝나거나 그냥 끝나는 게 정상이다.
  열에 아홉은 이메일 없이 끝나야 한다.
- 지어내지 않는다. 칭찬하지 않는다. 합격 가능성을 점치지 않는다.
- 연구실 이름은 "HAI Lab". "서울Tech" 금지.
- 한국어 질문에는 한국어, 영어 질문에는 영어.

[모범 답안 — 이 결을 그대로 따라라]

Q: 졸업생들은 어디로 갔나요?
A: 박사과정 진학과 기업 취업, 두 갈래예요. 진학은 싱가포르국립대와 본교 HAI Lab 으로,
취업은 게임(넷마블)·방산(LIG넥스원)·스타트업의 AI 엔지니어로 갔습니다.
비율이나 한 사람씩의 행선지는 위 목록의 Alumni 항목을 세어 답하라.

Q: 최근 CHI 논문이 궁금해요
A: CHI 2026에 포스터 2편이 실렸어요. LLM 에이전트 기반 UI 생성 연구와
지적장애인의 머리 움직임으로 적응 행동을 평가하는 연구예요.
전체 목록은 Publications 페이지에 있습니다.

Q: 요즘 어떤 연구를 하나요?
A: 지금 진행 중인 과제는 7건이에요. 굵직한 것은 과기정통부 60억 규모의
비전-언어-행동(VLA) 모델 과제와 산업부의 온디바이스 AI 출혈관리 과제고,
그 밖에 AI 튜터링·접근성 평가·의료 데이터 과제들이 있어요. Research > Projects 에 다 있습니다.

Q: 학부연구원 지원하고 싶어요
A: 매년 3월과 9월, 학기 시작에 맞춰 모집해요. 공고는 Board > News 에 올라오고,
시기가 아니어도 bogyeom@seoultech.ac.kr 로 미리 문의주시면 됩니다.

Q: How can I join the lab?
A: We recruit twice a year, in March and September. Openings are posted on Board > News,
and you are welcome to reach out anytime at bogyeom@seoultech.ac.kr.

Q: 오늘 저녁 메뉴 추천해줘
A: 저는 연구실 안내만 해드려요. HAI Lab 에 대해 궁금한 게 있으면 물어봐 주세요!

Q: 연구실 인원이 몇 명이에요?
A: 교수님 1분, 박사과정 4명, 석사과정 4명, 학부연구원 3명, 행정 직원 1분 — 모두 13명이에요.

Q: 연구실 분위기 어때요?
A: 그건 홈페이지만으로 답하긴 어렵지만, Board > Gallery 의 MT·홈커밍·생신 파티
사진을 보면 느낌이 올 거예요.`;
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
  async fetch(request, env, ctx) {
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

    const t0 = Date.now();
    const ask = clean[clean.length - 1].content;   // 방금 들어온 질문 (기록용)
    const isDemo = new URL(request.url).pathname === '/demo';

    // 데모는 사이트를 읽을 필요가 없다 — 연구 시연용 프롬프트만 쓴다
    let system;
    if (isDemo) {
      system = DEMO_RULES;
    } else {
      const idx = await getIndex();
      system = rules(digest(idx));
    }


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
        ...(isDemo ? { temperature: 0.7 } : {}),
      }),
    });

    if (!r.ok) {
      // 무엇이 잘못됐는지 남긴다. 이게 없으면 키 문제인지 잔액 문제인지 모델 이름
      // 문제인지 구분할 수 없어, 밖에서는 '잠시 후 다시' 만 보이고 끝난다.
      // 로그는 npx wrangler tail 로 본다. 방문자에게는 상태 코드까지만 알린다.
      const detail = await r.text().catch(() => '');
      console.error('upstream', r.status, detail.slice(0, 500));
      ctx.waitUntil(logAsk(env, {
        at: new Date().toISOString(), question: ask, answer: 'upstream ' + r.status,
        ms: Date.now() - t0, turn: clean.filter(m => m.role === 'user').length, ok: 0, punt: 0,
      }));
      return json({ error: '잠시 후 다시 시도해 주세요', upstream: r.status }, 502, head);
    }
    const data = await r.json();
    const answer = data?.choices?.[0]?.message?.content?.trim() || '답을 만들지 못했습니다.';

    ctx.waitUntil(logAsk(env, {
      at: new Date().toISOString(),
      question: (isDemo ? '[demo] ' : '') + ask,
      answer,
      ms: Date.now() - t0,
      turn: clean.filter(m => m.role === 'user').length,
      ok: 1,
      punt: isPunt(answer),
    }));

    return json({ answer }, 200, head);
  },
};

function json(obj, status, head) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { ...head, 'Content-Type': 'application/json; charset=utf-8' },
  });
}
