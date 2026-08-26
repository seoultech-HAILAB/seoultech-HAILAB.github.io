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
  document.querySelectorAll(".depth1 > li > .d1").forEach(function (a) {
    if (a.classList.contains("no-sub")) return;
    a.addEventListener("click", function (e) {
      e.preventDefault();
      var li = a.parentElement;
      var open = li.classList.contains("is-open");
      // 원본 tendina 와 동일하게 한 번에 하나만 펼친다
      document.querySelectorAll(".depth1 > li").forEach(function (o) { o.classList.remove("is-open"); });
      if (!open) li.classList.add("is-open");
    });
  });


  /* 하위 메뉴를 눌러 이동할 때, 그리고 마우스가 메뉴를 벗어날 때는 닫는다.
     안 그러면 이동한 페이지에서도 드롭다운이 펼쳐진 채로 남는다. */
  document.querySelectorAll(".depth2 a").forEach(function (a) {
    a.addEventListener("click", function () {
      document.querySelectorAll(".depth1 > li").forEach(function (o) { o.classList.remove("is-open"); });
    });
  });
  document.querySelectorAll(".depth1 > li").forEach(function (li) {
    li.addEventListener("mouseleave", function () { li.classList.remove("is-open"); });
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
    if (!ev.target.closest(".lnb")) {
      document.querySelectorAll(".depth1 > li").forEach(function (o) { o.classList.remove("is-open"); });
    }
  });

  /* ---------------------------------------------------- 3) V-log 슬라이드 */
  var mvp = document.querySelector(".mvp122");
  if (mvp) {
    var track = mvp.querySelector(".mvp_track");
    var items = track.children;
    var prev = mvp.querySelector(".mvp_prev");
    var next = mvp.querySelector(".mvp_next");
    var pos = 0;

    var perView = function () {
      var w = window.innerWidth;
      if (w <= 600) return 1;
      if (w <= 991) return 2;
      if (w <= 1200) return 3;
      return 4;
    };
    var maxPos = function () { return Math.max(0, items.length - perView()); };

    var render = function () {
      pos = Math.min(pos, maxPos());
      if (!items.length) return;
      var step = items[0].getBoundingClientRect().width + 22; // gap 22px
      track.style.transform = "translateX(" + (-pos * step) + "px)";
      prev.disabled = pos === 0;
      next.disabled = pos >= maxPos();
    };

    prev.addEventListener("click", function () { pos = Math.max(0, pos - 1); render(); });
    next.addEventListener("click", function () { pos = Math.min(maxPos(), pos + 1); render(); });

    var t;
    window.addEventListener("resize", function () {
      clearTimeout(t); t = setTimeout(render, 120);
    });
    // 썸네일 폭이 확정된 뒤에 계산해야 위치가 맞는다
    window.addEventListener("load", render);
    render();
  }

  /* ---------------------------------------------------- 4) 목록 필터 (다축)
     .filterbar[data-axis="year|cat|term"] 여러 개를 동시에 걸 수 있고,
     항목의 data-<axis> 값과 AND 로 결합한다. 고른 값은 주소에 남는다. */
  var flist = document.querySelector("[data-filter]");
  var bars = document.querySelectorAll(".filterbar");
  if (flist && bars.length) {
    var empty = document.querySelector(".empty");
    var rows = Array.prototype.slice.call(flist.children);
    var state = {};

    /* 목록이 길면 (뉴스 75, 갤러리 77, 논문 48) 끝까지 스크롤해야 한다.
       걸러진 것만 모아 쪽으로 끊고, 아래에 쪽 번호를 단다. */
    /* 사진·영상은 3열 격자라 3의 배수로 끊어야 마지막 줄이 안 깨진다.
       글 목록은 한 줄에 하나라 10개가 알맞다. */
    var PER = (flist.classList.contains("gallery") ||
               flist.classList.contains("vidlist") ||
               flist.classList.contains("acards")) ? 12 : 10;
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
      // 아래쪽까지 스크롤한 채로 필터를 바꾸면 화면이 안 변한 듯 보인다 → 목록 머리로 되돌린다
      var top = flist.getBoundingClientRect().top + window.scrollY - 140;
      if (window.scrollY > top) {
        window.scrollTo({ top: Math.max(0, top), behavior: reducedMotionGlobal() ? "auto" : "smooth" });
      }
    };

    bars.forEach(function (bar) {
      var axis = bar.getAttribute("data-axis") || "year";
      state[axis] = "all";
      bar.addEventListener("click", function (ev) {
        var btn = ev.target.closest(".fbtn");
        if (!btn) return;
        bar.querySelectorAll(".fbtn").forEach(function (b) { b.classList.toggle("is-on", b === btn); });
        state[axis] = btn.getAttribute("data-val");
        apply();
      });
      // 주소에 값이 있으면 초기 상태로 반영
      var init = new URL(window.location.href).searchParams.get(axis);
      if (init) {
        var initBtn = bar.querySelector('.fbtn[data-val="' + CSS.escape(init) + '"]');
        if (initBtn) {
          bar.querySelectorAll(".fbtn").forEach(function (b) { b.classList.toggle("is-on", b === initBtn); });
          state[axis] = init;
        }
      }
    });
    apply();
  }

  /* ---------------------------------------------------- 5) 갤러리 라이트박스 */
  var lb = document.getElementById("lightbox");
  if (lb) {
    var lbImg = lb.querySelector(".lb_img");
    var lbCap = lb.querySelector(".lb_cap");
    var btns = [], at = 0, opener = null;

    var lbVisible = function () {
      return Array.prototype.filter.call(document.querySelectorAll(".gitem"), function (f) {
        return !f.hidden;
      }).map(function (f) { return f.querySelector(".gbtn"); });
    };
    var lbShow = function (i) {
      if (!btns.length) return;
      at = (i + btns.length) % btns.length;
      lbImg.src = btns[at].getAttribute("data-full");
      lbImg.alt = btns[at].getAttribute("data-cap");
      lbCap.textContent = btns[at].getAttribute("data-cap");
    };
    var close = function () {
      lb.hidden = true;
      lbImg.removeAttribute("src");
      document.body.style.overflow = "";
      if (opener) opener.focus();
    };

    document.addEventListener("click", function (ev) {
      var b = ev.target.closest(".gbtn");
      if (b) {
        btns = lbVisible(); opener = b;
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

  /* ---------------------------------------------------- 6) AI 도우미 (데모) */
  var aiFab = document.getElementById("aiFab");
  var aiPanel = document.getElementById("aiPanel");
  if (aiFab && aiPanel) {
    var setAi = function (open) {
      aiPanel.hidden = !open;
      aiFab.setAttribute("aria-expanded", String(open));
      aiFab.setAttribute("aria-label", open ? "AI 도우미 닫기" : "AI 도우미 열기");
    };
    aiFab.addEventListener("click", function () { setAi(aiPanel.hidden); });
    aiPanel.querySelector(".ai_x").addEventListener("click", function () {
      setAi(false); aiFab.focus();
    });
    document.addEventListener("keydown", function (ev) {
      if (ev.key === "Escape" && !aiPanel.hidden) { setAi(false); aiFab.focus(); }
    });
  }

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
