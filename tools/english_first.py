#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""소식 글과 과제 글을 영어 먼저, 한글 나중으로 다시 짠다.

    python tools/english_first.py

이 사이트는 영어가 기본이다. 크롤해 온 글은 한글 본문 뒤에 영문 요약이 붙어 있었다.
  - board/news/*.html      본문 문단을 영문 → 구분선 → 한글 순으로 다시 놓는다.
                           사진 묶음(.post_gal)은 맨 앞에 그대로 둔다.
  - research/project/*.html 제목을 영문으로, 한글 제목은 그 아래 한 줄로. 본문은
                           역할·기간·재원 → 영문 요약 → 구분선 → 한글 → 사진.
  - research/index.html    과제 목록의 제목도 영문으로, 한글은 작은 줄로.
  - board/gallery/*.html   제목을 다듬은 영문으로, 한글 제목은 부제로. 목록·색인도 같이.
  - board/vlog/*.html      제목을 영문으로(VLOG_EN), 한글 제목은 부제로. 설명은 영문 먼저.
  - tools/post_index.json  과제·갤러리·V-log 제목을 영문으로 맞춘다.
문단 하나를 영문/한글로 가르는 기준은 한글 글자가 있느냐다. 주소만 있는 문단은 바로 앞
문단을 따라간다. 한 번 돌리면 다시 돌려도 바뀌지 않는다(구분선이 있으면 건너뛴다).
돌린 뒤에는 build_list_pages.py → build_home.py → tidy_pages.py 순으로 마무리한다.
"""
import difflib
import html
import io
import json
import os
import re
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEP = '<hr class="lang_sep">'                      # 옛 표식 — tidy 가 <hr> 을 지워 남지 않았다
# 한글 묶음 앞의 표식. tidy_pages(clean_post_html.tidy_flow) 는 글 없는 <hr>/<div> 를 걷어내므로
# 글이 든 <p> 로 둔다 — 이 표식이 있으면 이미 처리한 글이다. 선과 모양은 CSS(.lang_ko) 가 준다.
KO_OPEN, KO_CLOSE = '<p><span class="lang_ko">한국어</span></p>', ''
def done(s): return SEP in s or 'class="lang_ko"' in s

def rd(p): return io.open(os.path.join(ROOT, p), encoding="utf-8", newline="").read()
def wr(p, s):
    for n in range(5):                      # OneDrive 가 잠깐 잠그면 Errno 22 — 잠시 뒤 다시
        try:
            io.open(os.path.join(ROOT, p), "w", encoding="utf-8", newline="").write(s); return
        except OSError:
            if n == 4: raise
            time.sleep(1.5)
def plain(s): return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()
def has_ko(s): return re.search(r"[가-힣]", plain(s)) is not None
def has_en(s): return re.search(r"[A-Za-z]{2,}", plain(s)) is not None

BLOCK = re.compile(r'(<div class="post_gal">.*?</div>|<div class="post_video">.*?</div>|<blockquote>.*?</blockquote>|<p[^>]*>.*?</p>|<br\s*/?>|\s+)', re.S)

def tokens(body):
    out, pos = [], 0
    for m in BLOCK.finditer(body):
        if m.start() != pos:
            return None
        out.append(m.group(0)); pos = m.end()
    return out if pos == len(body) else None

def body_span(s):
    i = s.find('<div class="post_body">')
    j = s.find('<nav class="pnav"')
    if i < 0 or j < 0: return None
    i += len('<div class="post_body">')
    k = s.rfind("</div>", i, j)
    return i, k

def set_description(s, text):
    text = html.escape(re.sub(r"\s+", " ", text).strip()[:160], quote=True)
    return re.sub(r'(<meta name="description" content=")[^"]*(")', lambda m: m.group(1) + text + m.group(2), s, count=1)

# ───────────────────────── 소식 ─────────────────────────
EXTRA_EN = {  # 영문이 짧은 글에 보태는 번역 (글 번호 → 문단들)
    "154": [
        "The Human-centered AI Lab (HAI Lab, advisor: Prof. Kyoungwon Seo) in the Department of Applied Artificial Intelligence is recruiting undergraduate researchers. We study AI that understands and augments human behavior, cognition, and emotion in real-world settings such as healthcare, education, and manufacturing, using AI, Human-Computer Interaction, and AR/VR.",
        "<strong>1. Eligibility</strong> — SeoulTech undergraduates in their 3rd or 4th year (as of the 2026 academic year); students interested in AI and research; students considering graduate school.",
        "<strong>2. Benefits</strong> — a scholarship; a dedicated desk and research equipment (PC, GPU server, iPad, etc.; Sangsang Hall #410); opportunities to attend domestic and international conferences (e.g., ACM CHI), publish in top SCI journals, and file patents; joint research with partner institutions (Asan Medical Center, Hyundai Motor Company, UBC in Canada, etc.).",
        "<strong>3. Research areas and activities</strong> — Biomedical AI, AI for Education, Agentic AI, Vision-Language-Action models, and Immersive XR + AI. Undergraduate researchers join ongoing lab projects (LLM-based agents, AI model development) and take part in paper reviews and seminars.",
        "<strong>4. Schedule</strong> — Applications: April 1 (Wed) – April 12 (Sun), 2026, 12:00 PM. Document screening results: April 20 (Mon), 2026, 12:00 PM (individual notice). Interviews: scheduled individually with applicants who pass screening.",
        "<strong>5. How to apply</strong> — Application form: <a href=\"https://forms.gle/vwkdidKAWbBVZm8u8\" target=\"_blank\" rel=\"noopener\">https://forms.gle/vwkdidKAWbBVZm8u8</a>. Inquiries: Bogyeom Park, Ph.D. student, HAI Lab (bogyeom@seoultech.ac.kr).",
    ],
}

def reorder_news(path):
    s = rd(path)
    if done(s): return "skip"
    span = body_span(s)
    if not span: return "no body"
    i, k = span
    body = s[i:k]
    toks = tokens(body)
    if toks is None: return "unparsed"
    gal, en, ko, last = [], [], [], None
    for t in toks:
        if not t.strip(): continue
        if t.startswith('<div class="post_gal">'): gal.append(t); continue
        if t.startswith("<br"): continue
        if not plain(t): continue
        if has_ko(t): ko.append(t); last = ko
        elif has_en(t): en.append(t); last = en
        else: (last if last is not None else ko).append(t)   # 주소뿐인 문단은 앞 문단을 따른다
    seq = re.search(r"(\d+)\.html$", path).group(1)
    if seq in EXTRA_EN and not any(plain(EXTRA_EN[seq][0])[:40] in plain(t) for t in en):   # 이미 있으면 다시 안 붙인다
        en = ["<p>%s</p>" % p for p in EXTRA_EN[seq]] + en
    if not en: return "no english"
    new = "\n" + "".join(gal) + "".join(en) + ((KO_OPEN + "".join(ko) + KO_CLOSE) if ko else "") + "\n          "
    s = s[:i] + new + s[k:]
    s = set_description(s, plain(en[0]))
    wr(path, s)
    return "ok"

# ───────────────────────── 과제 ─────────────────────────
EN_TITLE_FIX = {  # 본문에서 못 꺼내거나 잘못 꺼내는 영문 제목
    "164": "Development of Video Intelligence Technology for Active Remote Learning",
}
ROLE = {"공동연구책임자": "Co-Principal Investigator", "연구책임자": "Principal Investigator",
        "참여연구원": "Participating Researcher", "공동연구원": "Co-Investigator", "공동연구자": "Co-Investigator"}
SPONSOR = {  # 메타 줄·목록 칩의 한글 기관명 → 영문. 긴 이름을 먼저 바꾼다.
    "서울특별시교육청 교육연구정보원": "Seoul Education Research & Information Institute (SMOE)",
    "한국교육학술정보원(KERIS)": "Korea Education and Research Information Service (KERIS)",
    "민관공동기술사업화(R&D)": "Public–Private Joint Tech Commercialization R&D",
    "서울과학기술대학교": "SeoulTech", "예술의전당": "Seoul Arts Center", "한국문화예술위원회": "Arts Council Korea",
    "과학기술정보통신부": "Ministry of Science and ICT", "서울특별시교육청": "Seoul Metropolitan Office of Education",
    "교육부": "Ministry of Education", "주식회사 성하": "SUNGHA", "주식회사 온클레브": "ONCLEV",
    "한국생산기술연구원": "KITECH", "기획재정부": "Ministry of Economy and Finance",
    "중소벤처기업부": "Ministry of SMEs and Startups", "주식회사 현대자동차": "Hyundai Motor Company",
    "한국연구재단": "National Research Foundation of Korea", "산업통상자원부": "Ministry of Trade, Industry and Energy",
    "튜터러스랩스": "Tutorus Labs", "아이센스": "i-SENS", "RISE 사업": "RISE Program",
}
def translate_terms(t):
    for a, b in ROLE.items(): t = t.replace(a, b)
    for a, b in SPONSOR.items(): t = t.replace(a, b)
    return t

def split_title(t):
    if not t.endswith(")"): return t, ""
    depth = 0
    for i in range(len(t) - 1, -1, -1):
        if t[i] == ")": depth += 1
        elif t[i] == "(":
            depth -= 1
            if depth == 0: return t[:i].strip(), t[i + 1:-1].strip()
    return t, ""

def project_titles():
    """번호 → (상태 머리, 한글 제목, 영문 제목)"""
    out = {}
    for f in sorted(os.listdir(os.path.join(ROOT, "research/project"))):
        if not f.endswith(".html"): continue
        seq = f[:-5]; s = rd("research/project/" + f)
        h = plain(re.search(r'<h3 class="post_tit">(.*?)</h3>', s, re.S).group(1))
        m = re.match(r"(\[[^\]]+\])\s*(.*)", h)
        status, ko_h = (m.group(1), m.group(2).strip()) if m else ("", h)
        if has_ko(ko_h):
            span = body_span(s); body = s[span[0]:span[1]]
            ps = [plain(p) for p in re.findall(r"<p[^>]*>(.*?)</p>", body, re.S)]
            en = ""
            for p in ps[:3]:
                k2, e2 = split_title(p)
                if (e2 and not has_ko(e2) and has_ko(k2) and not e2.startswith("KRW")
                        and difflib.SequenceMatcher(None, k2[:30], ko_h[:30]).ratio() >= 0.5):
                    en = e2; break
            en = EN_TITLE_FIX.get(seq, en)
            if not en: raise SystemExit("영문 제목 없음: " + f)
            out[seq] = (status, ko_h, en)
        else:
            out[seq] = (status, "", ko_h)   # 이미 영문
    return out

def reorder_project(path, status, ko, en):
    s = rd(path)
    if done(s): return "skip"
    span = body_span(s); i, k = span
    toks = tokens(s[i:k])
    if toks is None: return "unparsed"
    meta, en_b, ko_b, gal = [], [], [], []
    first = True
    for t in toks:
        if not t.strip(): continue
        if t.startswith('<div class="post_gal">'): gal.append(t); continue
        if t.startswith("<br"): continue
        p = plain(t)
        if not p: continue
        if first:                                   # 역할 / 기간 / 재원
            first = False
            meta.append(translate_terms(t)); continue
        if ko and p.startswith(ko[:12]) and split_title(p)[1]: continue   # 제목 줄은 머리로 갔다
        if "<strong>기간:</strong>" in t or p.startswith("기간:"):
            meta.append(t.replace("기간:", "Period:")); continue
        if "<strong>Funding:</strong>" in t or p.startswith("Funding:"):
            meta.append(translate_terms(t)); continue
        if p.rstrip(":") in ("English Summary", "영문 요약"): continue
        (ko_b if has_ko(t) else en_b).append(t)
    new = "\n" + "".join(meta) + "".join(en_b) + ((KO_OPEN + "".join(ko_b) + KO_CLOSE) if ko_b else "") + "".join(gal) + "\n          "
    s = s[:i] + new + s[k:]
    # 머리: 영문 제목, 그 아래 한글
    head = ("%s %s" % (status, en)).strip()
    s = re.sub(r'<h3 class="post_tit">.*?</h3>',
               lambda m: '<h3 class="post_tit">%s</h3>' % html.escape(head) + ('<p class="post_sub">%s</p>' % html.escape(ko) if ko else ""),
               s, count=1, flags=re.S)
    s = re.sub(r"<title>.*?</title>", lambda m: "<title>%s | SeoulTech HAI Lab</title>" % html.escape(head), s, count=1, flags=re.S)
    s = re.sub(r'(<meta property="og:title" content=")[^"]*(")', lambda m: m.group(1) + html.escape(head, quote=True) + m.group(2), s, count=1)
    if en_b: s = set_description(s, plain(en_b[0]))
    wr(path, s)
    return "ok"

# ───────────────────────── 갤러리 ─────────────────────────
GALLERY_EN = {  # 글 번호 → 영문 제목. 괄호 안 영문을 다듬은 것이다. 새 글은 여기에 한 줄 더한다.
    "188": "Completion of the 1st AURA Program", "189": "HAI Lab 2022 Spring Get-Together",
    "190": "HAI Lab 2022 Teachers' Day", "191": "Cheil Worldwide Visits HAI Lab",
    "192": "HAI Lab 2022 End-of-Semester Party", "193": "HAI Lab 2022 Summer Coffee Break",
    "194": "HAI Lab 2022 Photo Booth", "195": "Invited Seminar: Deb (UBC, Canada)",
    "196": "HAI Lab 2022 Homecoming", "197": "HAI Lab at KNA 2022 (Korean Neurological Association)",
    "198": "HAI Lab 2022 Autumn Outing", "199": "Invited Seminar: Prof. Sidney Fels (UBC, Canada)",
    "200": "HAI Lab 2022 Year-End Party", "201": "HAI Lab at HCI Korea 2023",
    "202": "HAI Lab 2023 Opening Week Party", "203": "Welcome Party for Prof. Martin Loeser (ZHAW, Switzerland)",
    "204": "Prof. Martin Loeser's First Time in Korea, Episode 1", "205": "Prof. Martin Loeser's First Time in Korea, Episode 2",
    "206": "HAI Lab 2023 Teachers' Day", "207": "HAI Lab 2023 NAVER Tour",
    "208": "SIGCHI Korea Local Chapter Event 2023", "209": "HAI Lab 2023 Welcome Party",
    "210": "Invited Seminar: Dr. Soojeong Yoo (UCLIC, UK)", "211": "Invited Seminar: NAVER LABS Interns",
    "212": "Invited Seminar: Dr. Joon-Ho Lim (ETRI, Korea)", "213": "Welcome Party for Minyoung Park",
    "214": "Invited Seminar: Seunghwan Roh (Adobe)", "215": "HAI Lab 2023 Fall Get-Together",
    "216": "HAI Lab 2023 Group Photo", "217": "HAI Lab at UIC EXPO 2023",
    "218": "HAI Lab at the ICT International Joint Research Conference 2023", "219": "HAI Lab 2023 Year-End Party",
    "220": "HAI Lab at HCI Korea 2024", "221": "HAI Lab 2024 Birthday Party",
    "222": "HAI Lab 2024 Welcome Party", "223": "HAI Lab 2024 Teachers' Day",
    "224": "HAI Lab at CHI 2024", "225": "HAI Lab 2024 Summer MT (Membership Training)",
    "226": "Graduation Celebration and Lab Manager Handover", "227": "Invited Seminar: Prof. Jihong Jeung (Tsinghua University, China)",
    "228": "Summer 2024 Commencement", "229": "Invited Seminar: Junghee Kim (Hyundai AutoEver)",
    "230": "Research Exchange Seminar with the Seoul Education Research & Information Institute", "231": "HAI Lab 2024 Year-End Party",
    "232": "HAI Lab at HCI Korea 2025", "233": "Invited Seminar: Soojeong Yoo and Callum Parker (University of Sydney)",
    "234": "Winter 2025 Commencement", "235": "Prof. Seo's 2025 Birthday Party",
    "236": "HAI Lab 2025 Badminton Tournament", "237": "HAI Lab at CHI 2025",
    "238": "HAI Lab 2025 Teachers' Day", "239": "HAI Lab 2025 Spring End-of-Semester Party",
    "240": "Invited Seminar: Dr. Diego Vilela Monteiro (ESIEA, France)", "241": "Lab Dinner and Badminton with Diego",
    "242": "Summer 2025 Commencement", "243": "HAI Lab Fall 2025 Dinner Gathering",
    "244": "HAI Lab at KSMTE 2025", "245": "HAI Lab Master's Graduation Party",
    "246": "HAI Lab's 1st Year-End Homecoming", "247": "HAI Lab at HCI Korea 2026",
    "248": "Research Exchange Workshop with SNB Lab", "249": "Invited Seminar: Prof. Sidney Fels (UBC, Canada)",
    "250": "Kimchi Academy Visit with Prof. Sidney Fels", "251": "Winter 2026 Commencement",
    "252": "Prof. Seo's 2026 Birthday Party", "253": "HAI Lab at CHI 2026",
    "254": "Invited Seminar: Lucy (Aalto University, Finland)", "260": "HAI Lab 2026 Teachers' Day",
    "261": "Visiting Ph.D. Researcher Event", "262": "Visit from Prof. Hyeong-gu Jeong (SNU)",
    "263": "i-SENS Project Meeting", "265": "Research Seminar with Prof. Huiyong Li's Group (Kyushu University, Japan)",
    "266": "Research Seminar with Prof. Dongwook Yoon (UBC, Canada)", "267": "Lunch with Our Undergraduate Researcher on Military Leave",
    "268": "HAI Lab 2026 Summer MT (Membership Training)", "269": "Summer 2026 Commencement",
}

def variants(t):
    return {t, html.escape(t, quote=False), html.escape(t, quote=True)}

def gallery_titles():
    """번호 → (옛 전체 제목 '한글 (English)', 한글, 영문). 이미 영문이면 건너뛴다."""
    out = {}
    for f in sorted(os.listdir(os.path.join(ROOT, "board/gallery"))):
        if not f.endswith(".html"): continue
        seq = f[:-5]; s = rd("board/gallery/" + f)
        h = plain(re.search(r'<h3 class="post_tit">(.*?)</h3>', s, re.S).group(1))
        if not has_ko(h):
            # 상세는 이미 영문 — 목록에 옛 제목이 남아 있으면 그것으로 마저 고친다
            lst = rd("board/gallery.html")
            m = re.search(r'<a href="gallery/%s\.html">(.*?)</a>' % seq, lst)
            if not m or not has_ko(plain(m.group(1))): continue
            sub = re.search(r'<p class="post_sub">(.*?)</p>', s)
            out[seq] = (plain(m.group(1)), plain(sub.group(1)) if sub else "", GALLERY_EN.get(seq, h))
            continue
        m = re.match(r"^(.*?)\s*\(([^()]*[A-Za-z][^()]*)\)\s*$", h)
        ko, en0 = (m.group(1).strip(), m.group(2).strip()) if m else (h, "")
        en = GALLERY_EN.get(seq) or en0
        if not en: raise SystemExit("갤러리 영문 제목 없음: " + f)
        out[seq] = (h, ko, en)
    return out

def english_gallery():
    titles = gallery_titles()
    if not titles:
        print("갤러리: 바꿀 것 없음"); return
    for seq, (old, ko, en) in titles.items():
        p = "board/gallery/%s.html" % seq; s = rd(p)
        s = re.sub(r'<h3 class="post_tit">.*?</h3>',
                   lambda m: '<h3 class="post_tit">%s</h3><p class="post_sub">%s</p>' % (html.escape(en), html.escape(ko)),
                   s, count=1, flags=re.S)
        for v in variants(old): s = s.replace(v, html.escape(en, quote=True))
        wr(p, s)
    for f in os.listdir(os.path.join(ROOT, "board/gallery")):          # 다른 글의 이전/다음 글
        if not f.endswith(".html"): continue
        p = "board/gallery/" + f; s = rd(p); s0 = s
        for seq, (old, ko, en) in titles.items():
            for v in variants(old): s = s.replace("<b>%s</b>" % v, "<b>%s</b>" % html.escape(en))
        if s != s0: wr(p, s)
    p = "board/gallery.html"; s = rd(p)                                 # 목록: 캡션, 라이트박스, alt
    for seq, (old, ko, en) in titles.items():
        for v in variants(old): s = s.replace(v, html.escape(en, quote=True))
    wr(p, s)
    p = "tools/post_index.json"; d = json.loads(rd(p))
    by_old = {old: en for (old, ko, en) in titles.values()}
    by_seq = GALLERY_EN
    for it in d.get("gallery2", []):
        m = re.match(r"^(\[[^\]]+\]\s*)(.*)$", it["title"])
        pre, t = (m.group(1), m.group(2)) if m else ("", it["title"])
        it["title"] = pre + (by_seq.get(str(it.get("seq")), None) if has_ko(t) else None or by_old.get(t, t))
    wr(p, json.dumps(d, ensure_ascii=False, indent=1) + "\n")
    print("갤러리: 제목 %d개를 영문으로 (한글은 상세 페이지 부제로)" % len(titles))

# ───────────────────────── V-log ─────────────────────────
VLOG_EN = {  # 글 번호 → (영문 제목, 영문 설명 문단들). 유튜브 제목·설명이 한글이라 여기서 옮긴다.
    "47": ("[CHI 2024] Day 1: An Açaí Bowl in Hawaii? ✈️",
           ["Prof. Kyoungwon Seo and five HAI Lab researchers on their overseas conference trip ⭐ Day one in Hawaii for CHI 2024 (May 11–16)!"]),
    "48": ("[CHI 2024] Day 2: Locked Out of the Conference Session… 😭",
           ["Prof. Kyoungwon Seo and five HAI Lab researchers on their overseas conference trip ⭐ Day two in Hawaii for CHI 2024 (May 11–16)! We headed for the Doctoral Consortium, but things did not go as planned…"]),
    "49": ("[CHI 2024] Day 3: HAI Lab Workshop in Hawaii 🎉",
           ["Prof. Kyoungwon Seo and five HAI Lab researchers on their overseas conference trip ⭐ Day three in Hawaii for CHI 2024 (May 11–16)! A workshop day with the professors. Will Dongyub and Doosung wrap up their workshop presentations successfully?!"]),
    "50": ("[CHI 2024] Day 4: The First Day of CHI at Last ❗❗",
           ["Prof. Kyoungwon Seo and five HAI Lab researchers on their overseas conference trip ⭐ Day four in Hawaii for CHI 2024 (May 11–16)! The first day of CHI 2024 at last! The long-awaited conference drew a huge crowd XD But the skies, clear until now, suddenly turned dark…"]),
    "51": ("[CHI 2024] Days 5–6: LBW Presentations and the Closing Party 🎶",
           ["Prof. Kyoungwon Seo and five HAI Lab researchers on their overseas conference trip ⭐ Days five and six in Hawaii for CHI 2024 (May 11–16)! On day five we toured the booths together. On day six Yuwon and Bogyeom gave their first LBW presentations. Day seven was all about moving luggage, so the Hawaii conference trip wraps up with day six."]),
    "52": ("[2024] A Lab That Goes to a Riverside Resort for Its Summer MT?",
           ["Prof. Kyoungwon Seo and ten HAI Lab researchers on the summer MT! We headed to a riverside resort in Gapyeong for the summer. After thrilling water activities came a fierce recreation contest with a day off on the line! Who will win the vacation day?"]),
    "77": ("[CHI 2025] A Family Trip to Japan (Disguised as a CHI 2025 Conference Diary)", []),
    "78": ("[HCI Korea 2026] The Conference Through a New Researcher's Eyes", []),
    "79": ("[HAI Lab] Off to a Legendary Start: CHI 2026 Conference Diary #Barcelona #Spain", []),
}
VLOG_DESC = " · A vlog by the researchers of the Human-centered AI Lab (HAI Lab), SeoulTech."

def english_vlog():
    titles = {}   # seq → (옛 제목, 한글, 영문)
    for f in sorted(os.listdir(os.path.join(ROOT, "board/vlog"))):
        if not f.endswith(".html"): continue
        seq = f[:-5]; s = rd("board/vlog/" + f)
        h = plain(re.search(r'<h3 class="post_tit">(.*?)</h3>', s, re.S).group(1))
        if not has_ko(h) or seq not in VLOG_EN: continue
        en, paras = VLOG_EN[seq]
        titles[seq] = (h, h, en)
        s = re.sub(r'<h3 class="post_tit">.*?</h3>',
                   lambda m: '<h3 class="post_tit">%s</h3><p class="post_sub">%s</p>' % (html.escape(en), html.escape(h)),
                   s, count=1, flags=re.S)
        s = re.sub(r"<title>.*?</title>", lambda m: "<title>%s | SeoulTech HAI Lab</title>" % html.escape(en), s, count=1, flags=re.S)
        s = re.sub(r'(<meta property="og:title" content=")[^"]*(")', lambda m: m.group(1) + html.escape(en, quote=True) + m.group(2), s, count=1)
        s = re.sub(r'(<iframe [^>]*title=")[^"]*(")', lambda m: m.group(1) + html.escape(en, quote=True) + m.group(2), s, count=1)
        span = body_span(s)
        if span and not done(s):
            i, k = span; body = s[i:k]
            toks = tokens(re.sub(r'<div class="post_video">.*?</div>', "", body, flags=re.S))
            vid = re.search(r'<div class="post_video">.*?</div>', body, re.S)
            ko_b = [t for t in (toks or []) if t.strip() and not t.startswith("<br") and plain(t)]
            en_b = ["<p>%s</p>" % html.escape(p) for p in paras]
            new = "\n" + (vid.group(0) if vid else "") + "".join(en_b) + ((KO_OPEN + "".join(ko_b) + KO_CLOSE) if ko_b else "") + "\n          "
            s = s[:i] + new + s[k:]
        s = set_description(s, en + VLOG_DESC)
        wr("board/vlog/" + f, s)
    if not titles:
        print("V-log: 바꿀 것 없음"); return
    for f in os.listdir(os.path.join(ROOT, "board/vlog")):          # 이전/다음 글
        if not f.endswith(".html"): continue
        p = "board/vlog/" + f; s = rd(p); s0 = s
        for seq, (old, ko, en) in titles.items():
            for v in variants(old): s = s.replace("<b>%s</b>" % v, "<b>%s</b>" % html.escape(en))
        if s != s0: wr(p, s)
    p = "board/vlog.html"; s = rd(p)                                 # 목록: alt, 제목
    for seq, (old, ko, en) in titles.items():
        for v in variants(old): s = s.replace(v, html.escape(en, quote=True))
    wr(p, s)
    p = "tools/post_index.json"; d = json.loads(rd(p))
    by_seq = {seq: en for seq, (old, ko, en) in titles.items()}
    for it in d.get("vlog2", []):
        if has_ko(it["title"]) and str(it.get("seq")) in by_seq: it["title"] = by_seq[str(it["seq"])]
    wr(p, json.dumps(d, ensure_ascii=False, indent=1) + "\n")
    print("V-log: 제목 %d개를 영문으로, 설명은 영문 먼저" % len(titles))

def main():
    # 소식
    tally = {}
    for f in sorted(os.listdir(os.path.join(ROOT, "board/news"))):
        if f.endswith(".html"):
            r = reorder_news("board/news/" + f); tally[r] = tally.get(r, 0) + 1
            if r not in ("ok", "skip"): print("  소식", f, r)
    print("소식:", tally)
    # 과제
    titles = project_titles()
    tally = {}
    for seq, (status, ko, en) in titles.items():
        r = reorder_project("research/project/%s.html" % seq, status, ko, en); tally[r] = tally.get(r, 0) + 1
        if r not in ("ok", "skip"): print("  과제", seq, r)
    print("과제:", tally)
    # 과제 제목이 쓰이는 다른 곳 — 목록, 이전/다음 글, 색인, 첫 화면
    ko2en = {ko: en for (_, ko, en) in titles.values() if ko}
    full = {("%s %s" % (st, ko)).strip(): ("%s %s" % (st, en)).strip() for (st, ko, en) in titles.values() if ko}
    lst = rd("research/index.html")
    for seq, (st, ko, en) in titles.items():
        if not ko: continue
        old = '<h4><a href="project/%s.html">%s</a></h4>' % (seq, html.escape(ko, quote=False))
        old2 = '<h4><a href="project/%s.html">%s</a></h4>' % (seq, ko)
        new = '<h4><a href="project/%s.html">%s</a></h4><p class="proj_ko">%s</p>' % (seq, html.escape(en, quote=False), html.escape(ko, quote=False))
        if old in lst: lst = lst.replace(old, new)
        elif old2 in lst: lst = lst.replace(old2, new)
        else: print("  목록에서 못 찾음:", seq)
        lst = lst.replace('alt="%s"' % ko, 'alt="%s"' % html.escape(en, quote=True)).replace('alt="%s"' % html.escape(ko, quote=True), 'alt="%s"' % html.escape(en, quote=True))
    lst = re.sub(r'<span class="tag">([^<]*)</span>',
                 lambda m: '<span class="tag">%s</span>' % html.escape(translate_terms(html.unescape(m.group(1))), quote=False), lst)
    wr("research/index.html", lst)
    for f in os.listdir(os.path.join(ROOT, "research/project")):
        if not f.endswith(".html"): continue
        s = rd("research/project/" + f); s0 = s
        for a, b in full.items():
            s = s.replace("<b>%s</b>" % html.escape(a), "<b>%s</b>" % html.escape(b)).replace("<b>%s</b>" % a, "<b>%s</b>" % html.escape(b))
        if s != s0: wr("research/project/" + f, s)
    p = "tools/post_index.json"; d = json.loads(rd(p))
    for it in d.get("projects2", []):
        it["title"] = full.get(it["title"], it["title"])
    wr(p, json.dumps(d, ensure_ascii=False, indent=1) + "\n")
    print("과제 제목 %d개를 목록·이전다음·색인에 반영" % len(full))
    english_gallery()
    english_vlog()

if __name__ == "__main__":
    main()
