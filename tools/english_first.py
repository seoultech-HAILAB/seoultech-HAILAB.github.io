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
  - tools/post_index.json  과제 제목을 영문으로 맞춘다.
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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEP = '<hr class="lang_sep">'

def rd(p): return io.open(os.path.join(ROOT, p), encoding="utf-8", newline="").read()
def wr(p, s): io.open(os.path.join(ROOT, p), "w", encoding="utf-8", newline="").write(s)
def plain(s): return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()
def has_ko(s): return re.search(r"[가-힣]", plain(s)) is not None
def has_en(s): return re.search(r"[A-Za-z]{2,}", plain(s)) is not None

BLOCK = re.compile(r'(<div class="post_gal">.*?</div>|<blockquote>.*?</blockquote>|<p[^>]*>.*?</p>|<br\s*/?>|\s+)', re.S)

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
    if SEP in s: return "skip"
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
    if seq in EXTRA_EN:
        en = ["<p>%s</p>" % p for p in EXTRA_EN[seq]] + en
    if not en: return "no english"
    new = "\n" + "".join(gal) + "".join(en) + ((SEP + "".join(ko)) if ko else "") + "\n          "
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
    if SEP in s: return "skip"
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
    new = "\n" + "".join(meta) + "".join(en_b) + ((SEP + "".join(ko_b)) if ko_b else "") + "".join(gal) + "\n          "
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

if __name__ == "__main__":
    main()
