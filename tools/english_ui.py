#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""사이트 공통 UI 문구를 영문으로 맞춘다 — 목록 머리줄, 필터, 쪽 이동, 이전/다음 글, 도우미, 푸터.

    python tools/english_ui.py

글 내용(소식·과제·갤러리 본문)은 english_first.py 가 맡고, 이 파일은 껍데기만 본다.
같은 문구를 만드는 도구(tidy_pages, build_post_pages, build_list_pages, build_history,
build_patents, main.js, search.js, ask.js)도 영문으로 고쳐 두었으므로, 이 파일은 옛 문구가
남아 있는 페이지를 잡아 주는 뒷정리다. 몇 번을 돌려도 결과는 같다.
build_history.py / build_patents.py 를 돌린 뒤에는 이 파일도 한 번 돌린다 — 사람 자료
(people_data.json)의 '석박통합' 같은 낱말은 거기서 그대로 나온다.
"""
import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PLAIN = [  # (옛 문구, 새 문구) — 그대로 바꾼다
    (">본문 바로가기<", ">Skip to content<"),
    ('aria-label="주요 메뉴"', 'aria-label="Main menu"'),
    ('aria-label="전체메뉴 열기"', 'aria-label="Open menu"'),
    ('aria-label="전체메뉴 닫기"', 'aria-label="Close menu"'),
    ('aria-label="HAI Lab 도우미"', 'aria-label="HAI Lab Assistant"'),
    ("<b>HAI Lab 도우미</b>", "<b>HAI Lab Assistant</b>"),
    ("최대한 신속하게 응답드리겠습니다", "We reply as quickly as we can"),
    ('aria-label="닫기"', 'aria-label="Close"'),
    ("안녕하세요, HAI Lab 안내 도우미입니다.<br>궁금한 것을 문의해 보세요!", "Hi, I'm the HAI Lab assistant.<br>Ask me anything about the lab!"),
    ("<span>대학원 지원은 어떻게 하나요?</span>", "<span>How do I apply to the graduate program?</span>"),
    ("<span>최근 CHI 논문이 궁금해요</span>", "<span>Tell me about recent CHI papers</span>"),
    ("<span>연구실 위치가 어디인가요?</span>", "<span>Where is the lab located?</span>"),
    ("메시지를 입력하세요.", "Type a message."),
    ('aria-label="AI 도우미 열기"', 'aria-label="Open AI assistant"'),
    ('aria-label="AI 도우미 닫기"', 'aria-label="Close AI assistant"'),
    ("232, Gongneung-ro, Nowon-gu, Seoul, Korea (공릉동, 서울과학기술대학교) 상상관 410호 인간중심 인공지능 연구실 (Human-centered Artificial Intelligence Lab., HAI Lab.)",
     "Human-centered AI Lab (HAI Lab), Sangsang Hall #410, Seoul National University of Science and Technology, 232 Gongneung-ro, Nowon-gu, Seoul, Korea (서울과학기술대학교 상상관 410호)"),
    ("<span>다음 글</span>", "<span>Next</span>"),
    ("<span>이전 글</span>", "<span>Previous</span>"),
    ('aria-label="글 이동"', 'aria-label="Post navigation"'),
    ('aria-label="다음 사진"', 'aria-label="Next photo"'),
    ('aria-label="이전 사진"', 'aria-label="Previous photo"'),
    ('aria-label="쪽 이동"', 'aria-label="Pagination"'),
    ('aria-label="이전 쪽"', 'aria-label="Previous page"'),
    ('aria-label="다음 쪽"', 'aria-label="Next page"'),
    ('<span class="fcap">구분</span>', '<span class="fcap">Type</span>'),
    ('<span class="fcap">연도</span>', '<span class="fcap">Year</span>'),
    ('<span class="fcap">진행</span>', '<span class="fcap">Status</span>'),
    ('aria-label="구분 선택"', 'aria-label="Filter by type"'),
    ('aria-label="연도 선택"', 'aria-label="Filter by year"'),
    ('aria-label="진행 선택"', 'aria-label="Filter by status"'),
    ('aria-pressed="true">전체</button>', 'aria-pressed="true">All</button>'),
    ('data-val="all">전체</button>', 'data-val="all">All</button>'),
    ("<span>번호</span>", "<span>No.</span>"),
    ("<span>구분</span>", "<span>Type</span>"),
    ("<span>제목</span>", "<span>Title</span>"),
    ("<span>날짜</span>", "<span>Date</span>"),
    ("<span>연도</span>", "<span>Year</span>"),
    ("<span>특허명</span>", "<span>Patent</span>"),
    ("<p>내용이 없습니다.</p>", "<p>No content.</p>"),
    ('<span class="is-here">현재 구성원</span>', '<span class="is-here">Current members</span>'),
    ("석박통합", "Integrated M.S.–Ph.D."),
    ("학석연계", "Combined B.S.–M.S."),
]
REGEX = [  # (정규식, 치환)
    (r"해당 연도의 소식이 없습니다\.", "No news for this year."),
    (r"해당 연도의 사진이 없습니다\.", "No photos for this year."),
    (r"해당 연도의 논문이 없습니다\.", "No publications for this year."),
    (r"해당 연도의 특허가 없습니다\.", "No patents for this year."),
    (r"해당 연도의 과제가 없습니다\.", "No projects for this year."),
    (r"등록번호 (\S+) \(등록일 ([^)]+)\)", r"Registration No. \1 (registered \2)"),
    (r"출원번호 (\S+) \(출원일 ([^)]+)\)", r"Application No. \1 (filed \2)"),
    (r"석사 졸업 (\d{4}\.\d{2})", r"M.S. graduated \1"),
    (r"(\d{4}\.\d{2})~현재", r"\1~present"),
    (r"(\d{4}\.\d{2}) ~ 현재", r"\1 ~ present"),
]

def fix(s):
    for a, b in PLAIN: s = s.replace(a, b)
    for a, b in REGEX: s = re.sub(a, b, s)
    return s

def main():
    n = 0
    for dp, dn, fn in os.walk(ROOT):
        rel = os.path.relpath(dp, ROOT).replace("\\", "/")
        if rel.split("/")[0] in ("output", "assets", "tools", ".git", ".wrangler", ".claude"): dn[:] = []; continue
        for f in fn:
            if not f.endswith(".html"): continue
            p = os.path.join(dp, f)
            s = io.open(p, encoding="utf-8", newline="").read(); t = fix(s)
            if t != s:
                io.open(p, "w", encoding="utf-8", newline="").write(t); n += 1
    print("UI 문구 영문화: %d장" % n)

if __name__ == "__main__":
    main()
