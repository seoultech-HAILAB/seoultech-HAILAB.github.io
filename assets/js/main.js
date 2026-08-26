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

    var apply = function () {
      var shown = 0;
      rows.forEach(function (el) {
        var hit = Object.keys(state).every(function (ax) {
          return state[ax] === "all" || el.getAttribute("data-" + ax) === state[ax];
        });
        el.hidden = !hit;
        if (hit) shown++;
      });
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
