# 이 사이트의 규칙

앞으로 글을 쓰거나 페이지를 더할 때 여기만 보면 된다.
값을 새로 정하지 말고 아래 이름을 쓴다. 이름이 없으면 그건 새로 만들 것이 아니라
이미 있는 것 중 하나를 써야 한다는 뜻이다.

---

## 1. 글 쓰는 법

사이트에 올라가는 모든 글 — News, Gallery 설명, 과제 소개, 데모 설명 — 이 따른다.

### 문장

**결론부터 쓴다.** 무슨 일이 있었는지가 첫 문장이다. 배경은 그 뒤에.

> ✅ 김유원 연구원이 CHI 2025 학생연구경진대회에서 2등상을 받았다.
> ❌ 지난 5월 요코하마에서 열린 CHI 2025 학회에서는 여러 세션이 진행되었는데, 그중
>    학생연구경진대회에서 우리 연구실의 김유원 연구원이 좋은 성과를 거두었다.

**빈말을 넣지 않는다.** 아래는 아무 정보가 없다. 지운다.

- "활발한 연구 활동을 이어가고 있습니다"
- "많은 관심 부탁드립니다"
- "뜻깊은 시간이었습니다"
- "앞으로도 최선을 다하겠습니다"

**칭찬하지 않는다.** 한 일을 적으면 읽는 사람이 알아서 판단한다.
"우수한 성과를 거둔" 대신 "상위 1% 저널에 게재된".

**숫자와 이름은 정확히.** 어림수를 쓰지 않는다.
"여러 편" → "7편", "많은 기관" → 기관 이름을 적거나 개수를 적는다.

### 길이

| 자리 | 길이 |
|---|---|
| 목록의 한 줄 (News 제목, 과제 제목) | 한 줄에 들어가게. 40자 안팎 |
| 카드의 설명 (`.demo_lead`, `.proj_desc`) | 두 문장 |
| 글 본문 문단 | 3~5문장. 넘으면 문단을 나눈다 |

### 표기

- **연구실 이름**: `HAI Lab` 또는 `서울과기대 HAI Lab`. "서울Tech"라고 쓰지 않는다.
- **날짜**: `2026.08.26` (점 구분). 세미나 페이지에 있던 `2026-08-26`은 쓰지 않는다.
- **사람 이름**: 영문 페이지는 로마자, 국문 글은 한글. 한 글 안에서 섞지 않는다.
  로마자 표기는 [tools/name_aliases.json](tools/name_aliases.json)이 기준이다.
- **학회**: `CHI 2026`, `HCI Korea 2026`, `AIED 2026`. 서로 다른 학회다. 섞지 않는다.
- **강조**: 한 문단에 `<b>`는 한 곳까지. 문단 절반이 굵으면 아무것도 강조되지 않는다.

---

## 2. 색

로고에서 뽑은 남색과 빨강, 그리고 회색. **이 셋 밖의 색을 새로 들이지 않는다.**

| 이름 | 값 | 쓰는 곳 |
|---|---|---|
| `--navy` | `#0c1854` | 가장 진한 남색. 채운 버튼, 강조 뱃지 |
| `--navy-ink` | `#17246b` | 링크, 제목 강조, 호버 |
| `--navy-tint` | `#e7eaf5` | 옅은 남색 판 (선택된 항목, 개수 뱃지) |
| `--navy-line` | `#ccd3e8` | 남색 계열 테두리 |
| `--red` | `#a81818` | 수상·모집처럼 드물게 눈에 띄어야 하는 것 |
| `--red-tint` / `--red-line` | | 위의 옅은 판·테두리 |
| `--ink` | `#1a1f2e` | 제목 글자 |
| `--ink-soft` | `#3a4256` | 본문 글자 |
| `--gray-ink` | `#5f6472` | 보조 글자 (날짜, 캡션, 라벨) |
| `--gray` | `#909090` | 가장 옅은 글자 (주석) |
| `--gray-line` | `#e2e5ec` | 모든 테두리와 구분선 |
| `--wash` | `#f7f9fd` | 옅은 바닥 (호버, 이미지 자리) |

`--azure`와 `--sand`는 옛 사이트에서 따라온 이름이다. 지금은 각각 남색·회색을 가리키게
해 뒀으니 **새로 쓰지 말고**, 손보는 김에 보이면 위 이름으로 바꾼다.

---

## 3. 글자

글꼴은 **NanumSquare 하나**다. 본문·제목·데모 전부 같다. serif를 섞지 않는다.

크기는 **역할로 고른다.** px를 직접 적지 않는다.

| 이름 | 값 | 쓰는 곳 |
|---|---|---|
| `--t-page` | 31px | 페이지 제목 (`Publications`, `Demos`) |
| `--t-sec` | 22px | 구역 제목 (`› 최근 소식`) |
| `--t-item` | 17.5px | 목록의 각 줄 제목, 논문 제목 |
| `--t-body` | 17px | 본문 |
| `--t-meta` | 14.5px | 날짜, 저자, 학회명 |
| `--t-small` | 13.5px | 버튼, 캡션, 주석 |
| `--t-label` | 11.5px | 태그, 뱃지, 대문자 라벨 |

**줄 길이는 `--line`(1000px)을 넘지 않는다.** 칸이 아무리 넓어도 글줄은 여기서 끊는다.
한글 55~60자 — 이보다 길면 다음 줄 첫머리를 찾기 어렵다.

---

## 4. 모양

모서리는 **다섯 단뿐**이다.

| 이름 | 값 | 쓰는 곳 |
|---|---|---|
| `--r-panel` | 14px | 카드, 패널, 대화창 |
| `--r-media` | 10px | 사진, 영상, 목록 행 |
| `--r-chip` | 5px | 뱃지, 태그 |
| `--r-pill` | 999px | 알약 버튼, 필터 |
| `--r-dot` | 50% | 동그라미 |

**카드는 한 모양이다.** 구성원·졸업생·과제·장비·데모가 모두 같다 —
흰 바닥, `--gray-line` 테두리, `--r-panel` 모서리, 호버 때 살짝 떠오름.
새 카드를 만들면 `.mcard, .acard, .fac, .proj` 규칙에 선택자를 하나 더 붙인다.
**새 카드 스타일을 따로 쓰지 않는다.**

---

## 5. 페이지 폭

| 자리 | 폭 |
|---|---|
| 페이지 전체 | `--read` (1440px), 좌우 여백은 `--gutter` |
| 글줄 | `--line` (1000px) |
| 데모 상세 | `--demo-col` (880px) — 제목부터 논문 목록까지 한 폭 |

**좌우 여백은 `--gutter` 한 곳에서만 정한다.** 넓은 화면에서는
`max(40px, (100% - --read) / 2)`, 900px 아래에서는 20px이다. 블록은 화면 끝까지
두고(배경이 꽉 차게) 안쪽 내용만 이 여백으로 모은다.

새 블록을 만들면 padding 을 새로 적지 말고
[extra.css](assets/css/extra.css)의 "좌우 여백" 목록에 **선택자 이름만 더한다.**
값을 블록마다 적어 두었더니 클래스 이름을 바꿀 때마다 목록에서 하나씩 조용히
빠졌다 — `.etc003`→`.sec_head` 때 PROJECTS·BOARD 머리가, `.mvp122`→`.boardfeat`
때 좁은 화면의 BOARD 카드가 그렇게 화면 끝까지 나갔다.

확인하는 법: 한 화면에서 블록들의 **안쪽 왼쪽 끝이 전부 같은 값**이어야 한다.

**한 페이지 안에서 오른쪽 끝이 셋 이상이면 잘못된 것이다.** 데모 상세가 그랬다 —
한 번 고친 뒤에도 1385 / 920 / 800 / 645로 네 군데가 남아 있었다. 지금은 페이지 머리와
`--demo-col` 둘뿐이다. 고친 뒤에는 실제로 세어 본다.

`ch` 단위를 쓰지 않는다. 요소마다 글꼴 크기가 달라 같은 `72ch`가 서로 다른 픽셀이 된다.

---

## 6. 저절로 따라오는 것

아래는 [extra.css](assets/css/extra.css) 끝의 "마감 규칙"이 사이트 전체에 걸어 둔 것이다.
새 컴포넌트를 만들어도 자동으로 적용된다. **다시 쓰지 않는다.**

- 키보드 포커스 테두리 (`:focus-visible`) — `outline: none`을 쓰지 않는다
- 드래그 선택 색 (`::selection`)
- 본문 속 링크 밑줄
- 이미지가 오기 전의 바닥색
- 표 모양
- 숫자 자릿수 맞춤 (`tabular-nums`)
- 움직임 줄이기 설정 존중 (`prefers-reduced-motion`)

---

## 7. 페이지를 더할 때

**손으로 HTML을 복사하지 않는다.** 네비게이션이 페이지마다 인라인이라 반드시 빠진다.
실제로 그렇게 만든 데모 페이지에서 메뉴에 글 제목이 박히고, 메뉴 항목이 누락됐다.

```bash
python tools/build_demos.py        # 데모를 더했을 때 (tools/demos_data.json 수정 후)
python tools/build_patents.py      # 특허를 더했을 때 (tools/patents_data.json 수정 후)
python tools/tidy_pages.py         # 항상 마지막에 — 네비·스크립트·캐시 번호를 맞춘다
python tools/build_search_index.py # 내용이 바뀌었으면 — 검색과 챗봇이 이걸 읽는다
```

`tidy_pages.py`가 전 페이지에 맞춰 주는 것: 네비게이션, 검색·도우미 스크립트,
`?v=` 캐시 번호, og 태그, 이전/다음 글 링크.

### CSS·JS를 고쳤으면 tidy까지가 한 세트다

`assets/` 아래 CSS나 JS를 한 글자라도 고쳤으면 **반드시** `tidy_pages.py`를 돌리고,
**바뀐 HTML까지 같이 커밋한다.**

```bash
# CSS 고침 → 여기까지가 하나의 변경이다
python tools/tidy_pages.py
git add assets/ *.html */*.html
```

`?v=` 뒤의 값은 그 파일 내용의 해시다. 파일이 바뀌면 값이 바뀌고, 그래야 브라우저가
새로 받는다. CSS만 커밋하고 HTML을 빼면 배포된 페이지는 **옛 번호를 계속 가리키므로**,
처음 온 사람에게는 새 디자인이, 다시 온 사람에게는 캐시에 남은 옛 디자인이 보인다.
겉으로는 아무 문제가 없어 보여서 알아채기 어렵다.

확인하는 법:

```bash
python - <<'PY'
import glob, hashlib, io, re
want = {f.split('/')[-1]: hashlib.md5(io.open(f, 'rb').read()).hexdigest()[:8]
        for f in glob.glob('assets/css/*.css') + glob.glob('assets/js/*.js')}
bad = []
for p in sorted(set(glob.glob('*.html') + glob.glob('*/*.html'))):
    s = io.open(p, encoding='utf-8').read()
    for n, h in want.items():
        for m in re.finditer(re.escape(n) + r'\?v=([a-z0-9]+)', s):
            if m.group(1) != h:
                bad.append((p, n, m.group(1), h))
print('스탬프 불일치:', len(bad), bad[:3])
PY
```

**챗봇은 `search-index.json`을 읽는다.** 페이지를 고치고 색인을 다시 만들지 않으면
도우미는 옛 내용으로 답한다. 그리고 색인은 **배포된 사이트**에서 읽으므로,
push 해야 반영된다.

---

## 8. 고칠 때 확인하는 것

```bash
# 네비게이션과 빵부스러기가 전 페이지에서 성한지
python - <<'PY'
import glob, io, re
EXPECT = {'Research Area','Facility','Patent','Professor','Researcher','Alumni','History',
          'Projects','Video','Demos','Publications','News','Gallery','V-log',
          'About','Members','Research','Board'}
for f in sorted(set(glob.glob('*.html') + glob.glob('*/*.html'))):
    s = io.open(f, encoding='utf-8').read()
    m = re.search(r'<nav [^>]*class="lnb".*?</nav>', s, re.S)
    items = re.findall(r'<li><a href="[^"]*"[^>]*>([^<]+)</a></li>', m.group(0)) if m else []
    bad = [x for x in items if x not in EXPECT]
    if bad or 'Demos' not in items:
        print(f, bad or '· Demos 누락')
PY
```

CSS를 고쳤으면 새 값이 위 표에 없는지 본다. 없으면 표에 추가하는 게 아니라
**있는 것 중 하나를 쓴다.**
