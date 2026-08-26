/* SeoulTech HAI Lab — 원본 사이트 동작 재현 (의존성 없음)
   1) 메인 비주얼 슬라이더  2) 좌측 GNB 아코디언  3) V-log 슬라이드  4) 모바일 전체메뉴 */
(function () {
  "use strict";

  function reducedMotionGlobal() {
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  /* ---------------------------------------------------- 1) 메인 비주얼 */
  var visual = document.querySelector(".mainVisual");
  if (visual) {
    var slides = visual.querySelectorAll(".slide");
    var dots = visual.querySelectorAll(".dot");
    var playBtn = visual.querySelector(".slide_play");
    var idx = 0, timer = null;
    var INTERVAL = 5000;

    var show = function (i) {
      idx = (i + slides.length) % slides.length;
      slides.forEach(function (s, n) { s.classList.toggle("is-on", n === idx); });
      dots.forEach(function (d, n) {
        d.classList.toggle("is-on", n === idx);
        d.setAttribute("aria-selected", String(n === idx));
      });
    };

    var reduced = function () {
      return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    };

    // byUser=true 는 재생 버튼을 직접 누른 경우.
    // 모션 감소 설정은 '알아서 돌지 마라'는 뜻이지 '눌러도 돌지 마라'가 아니므로,
    // 자동 시작만 막고 명시적 클릭은 그대로 따른다.
    var start = function (byUser) {
      stop();
      if (!byUser && reduced()) return;
      timer = setInterval(function () { show(idx + 1); }, INTERVAL);
      playBtn.dataset.playing = "true";
      playBtn.setAttribute("aria-label", "자동 재생 정지");
    };
    var stop = function () {
      if (timer) { clearInterval(timer); timer = null; }
      playBtn.dataset.playing = "false";
      playBtn.setAttribute("aria-label", "자동 재생 시작");
    };

    dots.forEach(function (d, n) {
      d.addEventListener("click", function () {
        var wasPlaying = playBtn.dataset.playing === "true";
        show(n);
        if (wasPlaying) start(true);
      });
    });
    playBtn.addEventListener("click", function () {
      if (timer) stop(); else start(true);
    });
    // 탭이 백그라운드면 굳이 돌리지 않는다
    document.addEventListener("visibilitychange", function () {
      if (document.hidden) { if (timer) { clearInterval(timer); timer = null; } }
      else if (playBtn.dataset.playing === "true") start(true);
    });

    start(false);
  }

  /* ---------------------------------------------------- 2) GNB 아코디언 */
  /* 펼침 상태를 클래스로만 표시하면 눈으로 보는 사람만 안다.
     화면 낭독기에도 같은 사실을 알려 준다. */
  var markOpen = function () {
    document.querySelectorAll(".depth1 > li").forEach(function (li) {
      var a = li.querySelector(":scope > .d1");
      if (!a || a.classList.contains("no-sub")) return;
      a.setAttribute("aria-expanded", String(li.classList.contains("is-open")));
    });
  };
  var closeAll = function () {
    document.querySelectorAll(".depth1 > li").forEach(function (o) { o.classList.remove("is-open"); });
    markOpen();
  };

  document.querySelectorAll(".depth1 > li > .d1").forEach(function (a) {
    if (a.classList.contains("no-sub")) return;
    a.setAttribute("aria-expanded", "false");
    a.setAttribute("aria-haspopup", "true");
    a.addEventListener("click", function (e) {
      e.preventDefault();
      var li = a.parentElement;
      var open = li.classList.contains("is-open");
      // 원본 tendina 와 동일하게 한 번에 하나만 펼친다
      closeAll();
      if (!open) li.classList.add("is-open");
      markOpen();
    });
  });


  /* 하위 메뉴를 눌러 이동할 때, 그리고 마우스가 메뉴를 벗어날 때는 닫는다.
     안 그러면 이동한 페이지에서도 드롭다운이 펼쳐진 채로 남는다. */
  document.querySelectorAll(".depth2 a").forEach(function (a) {
    a.addEventListener("click", closeAll);
  });
  document.querySelectorAll(".depth1 > li").forEach(function (li) {
    li.addEventListener("mouseleave", function () { li.classList.remove("is-open"); markOpen(); });
  });
  /* 하위 링크를 눌러 페이지를 옮기면 커서가 그 자리에 그대로 남는다. 그러면 새 페이지에서도
     :hover 가 참이라 드롭다운이 펼쳐진 채로 보인다. 마우스를 한 번이라도 움직이기 전까지는
     호버로 열리지 않게 잠가 둔다 (키보드 포커스는 그대로 열린다). */
  var unlock = function () {
    document.documentElement.classList.add("can-hover");
    window.removeEventListener("mousemove", unlock);
  };
  window.addEventListener("mousemove", unlock);
  document.addEventListener("click", function (ev) {
    if (!ev.target.closest(".lnb")) closeAll();
  });

  /* 3) 홈의 V-log 가로 슬라이드(.mvp122)는 3열 카드(.boardfeat)로 바뀌면서 사라졌다.
        여기 있던 슬라이더 코드는 어느 페이지에서도 걸리지 않아 걷어냈다. */

  /* ---------------------------------------------------- 4) 목록 필터 (다축)
     .filterbar[data-axis="year|cat|term"] 여러 개를 동시에 걸 수 있고,
     항목의 data-<axis> 값과 AND 로 결합한다. 고른 값은 주소에 남는다. */
  var flist = document.querySelector("[data-filter]");
  var bars = document.querySelectorAll(".filterbar");
  /* 사진 크게보기가 쪽 경계를 넘어갈 수 있게, 아래 필터 블록이 여기에
     '몇 번째 항목이 있는 쪽으로 옮겨라' 를 걸어 둔다. */
  var goToItemPage = null;
  if (flist && bars.length) {
    var empty = document.querySelector(".empty");
    var rows = Array.prototype.slice.call(flist.children);
    var state = {};

    /* 목록이 길면 (뉴스 75, 갤러리 77, 논문 48) 끝까지 스크롤해야 한다.
       걸러진 것만 모아 쪽으로 끊고, 아래에 쪽 번호를 단다. */
    /* 사진·영상은 3열 격자라 3의 배수로 끊어야 마지막 줄이 안 깨진다.
       글 목록은 한 줄에 하나라 10개가 알맞다. */
    var PER = (flist.classList.contains("gallery") ||
               flist.classList.contains("vids") ||
               flist.classList.contains("acards")) ? 9 : 10;
    var page = 1;
    var pager = document.createElement("nav");
    pager.className = "pager";
    pager.setAttribute("aria-label", "쪽 이동");
    flist.parentNode.insertBefore(pager, flist.nextSibling);

    var drawPager = function (total) {
      var last = Math.max(1, Math.ceil(total / PER));
      if (page > last) page = last;
      if (last <= 1) { pager.hidden = true; pager.innerHTML = ""; return; }
      pager.hidden = false;
      var html = '<button class="pg pg_nav" data-go="' + (page - 1) + '"' +
                 (page === 1 ? " disabled" : "") + ' aria-label="이전 쪽">‹</button>';
      var marks = [];
      for (var i = 1; i <= last; i++) marks.push(i);
      marks.forEach(function (i) {
        html += i === "…"
          ? '<span class="pg_gap">…</span>'
          : '<button class="pg' + (i === page ? " is-on" : "") + '" data-go="' + i +
            '"' + (i === page ? ' aria-current="page"' : "") + ">" + i + "</button>";
      });
      html += '<button class="pg pg_nav" data-go="' + (page + 1) + '"' +
              (page === last ? " disabled" : "") + ' aria-label="다음 쪽">›</button>';
      pager.innerHTML = html;
    };

    pager.addEventListener("click", function (ev) {
      var b = ev.target.closest("[data-go]");
      if (!b || b.disabled) return;
      page = parseInt(b.getAttribute("data-go"), 10);
      apply(true);
    });

    var apply = function (keepPage) {
      if (!keepPage) page = 1;
      var shown = 0;
      rows.forEach(function (el) {
        var hit = Object.keys(state).every(function (ax) {
          return state[ax] === "all" || el.getAttribute("data-" + ax) === state[ax];
        });
        el.hidden = !hit;
        // 쪽 나누기로 숨기기 전에 '걸러서 남은 것' 을 표시해 둔다.
        // 사진 크게보기는 이 표시를 보고 쪽 너머까지 넘긴다.
        el.dataset.hit = hit ? "1" : "0";
        if (hit) shown++;
      });
      // 걸러진 것 중 이번 쪽에 해당하는 구간만 남긴다
      var seen = 0, from = (page - 1) * PER, to = from + PER;
      rows.forEach(function (el) {
        if (el.hidden) return;
        var i = seen++;
        if (i < from || i >= to) el.hidden = true;
      });
      drawPager(shown);
      if (empty) empty.hidden = shown !== 0;
      // 필터가 먹었는지 눈으로 바로 확인되도록 개수를 표시한다
      document.querySelectorAll(".fcount").forEach(function (el) {
        el.textContent = shown === rows.length
          ? "전체 " + rows.length + "건"
          : shown + " / " + rows.length + "건";
        el.classList.toggle("is-filtered", shown !== rows.length);
      });

      var url = new URL(window.location.href);
      Object.keys(state).forEach(function (ax) {
        if (state[ax] === "all") url.searchParams.delete(ax);
        else url.searchParams.set(ax, state[ax]);
      });
      history.replaceState(null, "", url);
      // 아래쪽까지 스크롤한 채로 필터를 바꾸면 화면이 안 변한 듯 보인다 → 목록 머리로 되돌린다.
      // 단, 사진을 크게 본 채로 쪽을 넘길 때는 뒤에서 화면이 움직일 이유가 없다.
      var lbOpen = document.getElementById("lightbox");
      if (lbOpen && !lbOpen.hidden) return;
      var top = flist.getBoundingClientRect().top + window.scrollY - 140;
      if (window.scrollY > top) {
        window.scrollTo({ top: Math.max(0, top), behavior: reducedMotionGlobal() ? "auto" : "smooth" });
      }
    };

    bars.forEach(function (bar) {
      var axis = bar.getAttribute("data-axis") || "year";
      state[axis] = "all";
      // 고른 것을 클래스로만 표시하면 화면 낭독기는 무엇이 걸렸는지 알 수 없다
      var pick = function (btn) {
        bar.querySelectorAll(".fbtn").forEach(function (b) {
          b.classList.toggle("is-on", b === btn);
          b.setAttribute("aria-pressed", String(b === btn));
        });
      };
      bar.addEventListener("click", function (ev) {
        var btn = ev.target.closest(".fbtn");
        if (!btn) return;
        pick(btn);
        state[axis] = btn.getAttribute("data-val");
        apply();
      });
      pick(bar.querySelector(".fbtn.is-on"));
      // 주소에 값이 있으면 초기 상태로 반영
      var init = new URL(window.location.href).searchParams.get(axis);
      if (init) {
        var initBtn = bar.querySelector('.fbtn[data-val="' + CSS.escape(init) + '"]');
        if (initBtn) {
          pick(initBtn);
          state[axis] = init;
        }
      }
    });

    // 사진 크게보기가 쪽 경계를 넘을 때 목록도 그 쪽으로 따라 넘어가게 한다
    goToItemPage = function (i) {
      var want = Math.floor(i / PER) + 1;
      if (want === page) return;
      page = want;
      apply(true);
    };

    apply();
  }

  /* ---------------------------------------------------- 5) 갤러리 라이트박스 */
  var lb = document.getElementById("lightbox");
  if (lb) {
    var lbImg = lb.querySelector(".lb_img");
    var lbCap = lb.querySelector(".lb_cap");
    var btns = [], at = 0, opener = null;

    /* 목록에서는 <button class="gbtn">, 글 본문에서는 격자 안의 <img> 를 넘긴다.
       둘 다 '큰 그림 주소'와 '설명'을 읽어 오는 방식만 다르고 나머지는 같다. */
    var srcOf = function (el) {
      return el.getAttribute("data-full") || el.getAttribute("src");
    };
    var capOf = function (el) {
      return el.getAttribute("data-cap") || el.getAttribute("alt") || "";
    };
    var lbVisible = function (from) {
      if (from && from.closest(".post_gal")) {
        return Array.prototype.slice.call(from.closest(".post_gal").querySelectorAll("img"));
      }
      /* 쪽 나누기가 이번 쪽 말고는 다 hidden 으로 만들기 때문에, 보이는 것만 모으면
         한 쪽 안에서만 빙빙 돌았다. 필터를 통과한 것 전부(data-hit="1")를 모아
         쪽 경계를 넘어 계속 넘길 수 있게 한다. */
      var all = document.querySelectorAll('.gitem[data-hit="1"]');
      if (!all.length) {                       // 필터·쪽 나누기가 없는 페이지
        all = Array.prototype.filter.call(document.querySelectorAll(".gitem"),
                                          function (f) { return !f.hidden; });
      }
      return Array.prototype.map.call(all, function (f) { return f.querySelector(".gbtn"); });
    };
    var lbShow = function (i) {
      if (!btns.length) return;
      at = (i + btns.length) % btns.length;
      lbImg.src = srcOf(btns[at]);
      lbImg.alt = capOf(btns[at]);
      var inPost = btns[at].closest(".post_gal");
      // 목록에서는 지금 몇 번째인지도 함께 — 쪽을 넘어 다니므로 위치가 보여야 한다
      lbCap.textContent = inPost
        ? (at + 1) + " / " + btns.length
        : capOf(btns[at]) + "  (" + (at + 1) + " / " + btns.length + ")";
      // 다른 쪽의 사진으로 넘어갔으면 뒤의 목록도 그 쪽으로 옮겨 둔다
      if (!inPost && goToItemPage) goToItemPage(at);
    };
    var close = function () {
      lb.hidden = true;
      lbImg.removeAttribute("src");
      document.body.style.overflow = "";
      if (opener) opener.focus();
    };

    document.addEventListener("click", function (ev) {
      var b = ev.target.closest(".gbtn") || ev.target.closest(".post_gal img");
      if (b) {
        btns = lbVisible(b); opener = b;
        lbShow(btns.indexOf(b));
        lb.hidden = false;
        document.body.style.overflow = "hidden";
        lb.querySelector(".lb_close").focus();
        return;
      }
      if (ev.target.closest(".lb_close")) return close();
      if (ev.target.closest(".lb_prev")) return lbShow(at - 1);
      if (ev.target.closest(".lb_next")) return lbShow(at + 1);
      if (ev.target === lb) close();
    });
    document.addEventListener("keydown", function (ev) {
      if (lb.hidden) return;
      if (ev.key === "Escape") close();
      else if (ev.key === "ArrowLeft") lbShow(at - 1);
      else if (ev.key === "ArrowRight") lbShow(at + 1);
    });
  }

  /* 6) 도우미는 assets/js/ask.js 가 맡는다. 여기에도 여닫기 코드가 남아 있어
        버튼 한 번에 두 번 토글되는 바람에 패널이 열리지 않았다. */

  /* ---------------------------------------------------- 7) 모바일 전체메뉴 */
  var toggle = document.querySelector(".m-toggle");
  var lnb = document.getElementById("lnb");
  if (toggle && lnb) {
    toggle.addEventListener("click", function () {
      var open = lnb.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", String(open));
      toggle.setAttribute("aria-label", open ? "전체메뉴 닫기" : "전체메뉴 열기");
    });
  }
})();
