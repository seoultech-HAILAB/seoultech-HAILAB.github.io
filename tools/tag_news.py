#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""News 의 갈래 태그·강조·NEW 를 홈과 목록에 함께 단다.

    python tools/tag_news.py

홈 첫 화면의 NEWS 여덟 줄에는 갈래 태그와 제목 속 강조가 붙어 있는데, 정작 전체
목록 75줄은 같은 무게의 제목만 늘어서 있었다. 무엇이 논문이고 무엇이 수상인지
한 줄씩 읽어야 알 수 있었다. 두 화면이 어긋나지 않도록 여기서 둘 다 만든다.

  1. 제목을 보고 갈래를 정한다 (RULES — 위에서부터 먼저 맞는 것이 이긴다)

       Paper    논문 게재·게재 확정            남색 채움
       Grant    연구비 수주                    남색 옅은 채움
       Talk     학회 발표·워크숍·강연          남색 테두리
       Award    수상·장학·표창                 빨강 채움
       Member   새 식구 (여럿이면 Members)     빨강 옅은 채움
       Etc.     모집·언론·그 밖                회색 테두리

  2. Paper·Award·Grant 줄의 핵심 어구를 <em class="nkey"> 로 감싼다.
     학술지와 등급, 상 이름, 연구비를 준 곳 — 그 줄에서 먼저 읽어야 할 것들이다.
     테두리 태그(Talk·Etc.)와 사람 줄(Member)에는 넣지 않는다. 이름과 학회명은
     제목 자체가 이미 그 말이라, 강조를 더하면 줄마다 색칠이 되어 오히려 안 읽힌다.

  3. 예전에 있던 NEW 배지는 걷어낸다. 날짜가 같은 줄 오른쪽 끝에 있어 배지가
     더 알려 주는 것이 없었고, 정적 사이트라 '최근' 이 손으로 관리되어 홈과
     목록이 서로 다른 글에 배지를 달 위험만 남았다.

몇 번을 돌려도 결과가 같다 (붙어 있던 표식을 먼저 걷어내고 다시 단다).
"""
import html as html_mod
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIST = os.path.join(ROOT, "board", "index.html")
HOME = os.path.join(ROOT, "index.html")

# 위에서부터 먼저 맞는 것이 이긴다 — 순서가 곧 규칙이다.
RULES = [
    # 연구비 수주도 'Awarded' 로 시작한다. 수상보다 먼저 걸러내지 않으면
    # 연구비 열한 건이 전부 빨간 Award 가 된다.
    (r"\b(?:Research\s+)?Grant\b", "grant"),
    # 논문 — 게재(Publishes Paper in) 와 게재 확정(Accepted) 만.
    # 'Papers Have Been Presented' 는 학회 발표라 아래 Talk 로 간다.
    (r"\bPublishe?s?\s+Paper\b|\bPapers?\s+(?:Have|Has)\s+Been\s+Accepted\b", "paper"),
    # 수상 — 상·장학금·표창. 'Outstanding Presentation Award' 처럼 발표 낱말이
    # 섞여 있어도 상이 먼저다.
    (r"\bAwards?\b|\bScholarship\b|\bCommendation\b|\bPrize\b", "award"),
    # 새 식구 — 들어온 글은 예외 없이 'Welcome Aboard!' 로 끝난다
    (r"\bWelcome Aboard\b", "member"),
    # 발표 — 학회 발표, 워크숍·부스 주최, 기조강연, 초청 강연
    (r"\bPresent(?:ed|s|ing)?\b|\bHosts?\b|\bHosted\b|\bKeynote\b"
     r"|\bSpeaks?\b|\bWorkshop\b|\bBooth\b|\bLecture\b", "talk"),
]
DEFAULT_KIND = "etc"          # 모집·언론·그 밖

# 제목 속 강조. 규칙마다 처음 맞는 곳 한 번씩만 감싼다.
KEY_PATTERNS = {
    "paper": [
        r"(?<=Paper in )(.+?)(?= \()",              # 학술지 이름
        r"(?<=\()(SSCI[^()]*|SCIE[^()]*)(?=\))",    # 등급
        r"(?<=Been Accepted at )(.+)$",             # 게재 확정된 학회
    ],
    "award": [
        r"(?<=Awarded )(.+? Award)\b",
        r"(?<=Received )(.+? Award)\b",
        r"(?<=Wins )(.+? Award)\b",
        r"(?<=Selected for the )(.+)$",
        r"(?<=Honored with )(Commendation)\b",
    ],
    "grant": [
        r"(?<=Grant from )(.+?)(?= for )",          # 연구비를 준 곳
        r"(?<=Awarded )(NRF)(?=\s)",                # 'from' 없이 바로 NRF 인 줄
    ],
}

TAG_RE = re.compile(r'<span class="ntag[^"]*">[^<]*</span>')
NEW_RE = re.compile(r'<span class="nnew">NEW</span>')
KEY_RE = re.compile(r'<em class="nkey">(.*?)</em>', re.S)

LIST_ROW = re.compile(
    r'(<li class="lrow" data-year="\d+">)(.*?)(<span class="lno">\d+</span>)'
    r'(.*?)(<p>)(.*?)(</p>)(<time>[\d.]+</time></li>)', re.S)
# 주소를 news/숫자 로 못박는다. [^"]+ 로 두었더니 상단 메뉴의
# <li><a href="board/index.html">News</a></li> 부터 물어, 메뉴 안에 태그가 박히고
# 정작 첫 소식은 태그를 잃었다. 태그 자리도 '있거나 없거나' 로 좁혀 둔다.
HOME_ROW = re.compile(
    r'(<li><a href="board/(news/\d+\.html)">)'
    r'((?:<span class="ntag[^"]*">[^<]*</span>)?)'
    r'(<span class="nsub"><span class="subject">)(.*?)(</span>)', re.S)


def strip_marks(s):
    """붙어 있던 표식을 걷어낸다 — 몇 번을 돌려도 같은 결과가 나오게."""
    return KEY_RE.sub(r"\1", NEW_RE.sub("", TAG_RE.sub("", s)))


def plain(s):
    return html_mod.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def classify(title):
    for pat, kind in RULES:
        if re.search(pat, title, re.I):
            return kind
    return DEFAULT_KIND


def label(kind, title):
    """Member 만 사람 수를 센다. 제목의 동사는 한 명이어도 'Join' 이라 셀 수 없어서,
    'Join' 앞의 이름을 쉼표·& 로 끊어 헤아린다."""
    if kind != "member":
        return {"paper": "Paper", "grant": "Grant", "talk": "Talk",
                "award": "Award", "etc": "Etc."}[kind]
    head = re.split(r"\bJoins?\b", plain(title))[0]
    names = [n for n in re.split(r",|&|\band\b", head) if n.strip()]
    return "Members" if len(names) > 1 else "Member"


def add_keys(title, kind):
    for pat in KEY_PATTERNS.get(kind, []):
        m = re.search(pat, title)
        if not m or "<em" in m.group(1):
            continue
        s, e = m.span(1)
        title = title[:s] + '<em class="nkey">' + m.group(1) + "</em>" + title[e:]
    return title


def tag(title, kind):
    return '<span class="ntag ntag-%s">%s</span>' % (kind, label(kind, title))


def tag_home(tally):
    """홈 NEWS 여덟 줄.
    돌려주는 값은 (주소 -> 갈래) — 목록이 같은 판단을 쓰는지 맞춰 보는 데 쓴다."""
    raw = io.open(HOME, encoding="utf-8", newline="").read()
    crlf = "\r\n" in raw
    s = raw.replace("\r\n", "\n")
    kinds = {}

    def one(m):
        head, href, mid, sub_open, title, sub_close = m.groups()
        mid, title = strip_marks(mid), strip_marks(title)
        kind = classify(plain(title))
        kinds[href] = kind
        tally[kind] = tally.get(kind, 0) + 1
        return head + tag(title, kind) + mid + sub_open + add_keys(title, kind) + sub_close

    s2, n = HOME_ROW.subn(one, s)
    s2 = NEW_RE.sub("", s2)      # 옛 NEW 배지가 남아 있으면 여기서 사라진다
    io.open(HOME, "w", encoding="utf-8", newline="").write(
        s2.replace("\n", "\r\n") if crlf else s2)
    print("홈 %d줄" % n)
    return kinds


def tag_list(kinds, tally):
    raw = io.open(LIST, encoding="utf-8", newline="").read()
    crlf = "\r\n" in raw
    s = raw.replace("\r\n", "\n")

    # 머리글에 '구분' 칸 (CSS 가 이 이름을 보고 칸을 하나 더 낸다)
    s = s.replace('<div class="lhead lhead--news"><span>번호</span><span>제목</span>',
                  '<div class="lhead lhead--news"><span>번호</span><span>구분</span>'
                  '<span>제목</span>', 1)
    s = s.replace('<ul class="llist" data-filter="year">',
                  '<ul class="llist llist--news" data-filter="year">', 1)

    def one(m):
        head, mid1, lno, mid2, po, body, pc, tail = m.groups()
        mid1, mid2, body = strip_marks(mid1), strip_marks(mid2), strip_marks(body)
        a = re.search(r'<a href="([^"]+)">(.*?)</a>', body, re.S)
        href = a.group(1) if a else ""
        title = a.group(2) if a else body
        kind = classify(plain(title))
        if href in kinds and kinds[href] != kind:
            raise SystemExit("홈과 목록의 갈래가 다르다: %s" % href)
        tally[kind] = tally.get(kind, 0) + 1
        marked = add_keys(title, kind)
        body = ('<a href="%s">%s</a>' % (href, marked)) if a else marked
        return head + mid1 + lno + tag(title, kind) + mid2 + po + body + pc + tail

    s2, n = LIST_ROW.subn(one, s)
    if not n:
        raise SystemExit("목록 줄을 찾지 못했다 — board/index.html 모양이 바뀌었는지 확인")
    io.open(LIST, "w", encoding="utf-8", newline="").write(
        s2.replace("\n", "\r\n") if crlf else s2)
    print("목록 %d줄" % n)


def main():
    home_tally, list_tally = {}, {}
    kinds = tag_home(home_tally)
    tag_list(kinds, list_tally)
    for k, name in (("paper", "Paper"), ("grant", "Grant"), ("talk", "Talk"),
                    ("award", "Award"), ("member", "Member(s)"), ("etc", "Etc.")):
        print("  %-9s %2d" % (name, list_tally.get(k, 0)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
