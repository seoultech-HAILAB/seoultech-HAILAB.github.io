/* 홈 사이트 검색.
 * GitHub Pages 는 정적이라 검색 서버가 없다. 빌드 때 만들어 둔
 * assets/search-index.json 을 첫 입력 시 한 번만 받아 브라우저에서 찾는다.
 * 색인은 tools/build_search_index.py 가 생성한다. */
(function () {
  var input = document.getElementById("ssq");
  var box = document.getElementById("ssResults");
  if (!input || !box) return;

  // 하위 폴더 페이지에서도 색인과 결과 링크가 맞도록 사이트 루트를 알아낸다.
  // 이 파일은 항상 <root>/assets/js/search.js 로 실려 있다.
  var me = document.currentScript ||
           document.querySelector('script[src*="search.js"]');
  var BASE = me ? me.getAttribute("src").replace(/assets\/js\/search\.js.*$/, "") : "";

  var data = null, pending = null;

  function load() {
    if (data) return Promise.resolve(data);
    // 받아오는 중에 또 부르면, 예전에는 곧바로 null 을 돌려줘서 방금 친 검색어가
    // '결과 없음' 이 되고 먼저 걸린 요청이 옛 검색어로 결과를 그렸다.
    // 진행 중인 약속을 그대로 돌려주면 둘 다 같은 결과를 기다린다.
    if (pending) return pending;
    pending = fetch(BASE + "assets/search-index.json")
      .then(function (r) { return r.json(); })
      .then(function (j) { data = j; pending = null; return j; })
      .catch(function () { pending = null; return null; });
    return pending;
  }

  function esc(s) {
    return s.replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  // 검색어를 결과 안에서 굵게 — 어디가 걸렸는지 보이게 한다
  function mark(text, q) {
    var i = text.toLowerCase().indexOf(q);
    if (i < 0) return esc(text);
    return esc(text.slice(0, i)) + "<mark>" + esc(text.slice(i, i + q.length)) +
           "</mark>" + esc(text.slice(i + q.length));
  }

  function render(q) {
    if (!data || q.length < 2) { box.hidden = true; box.innerHTML = ""; return; }
    var lq = q.toLowerCase();
    var hits = [];
    for (var i = 0; i < data.length && hits.length < 40; i++) {
      // a 는 한글 표기 같은 숨은 검색어다 ('박보겸' 으로 'Bogyeom Park' 이 걸리게).
      // 색인은 만들어 두고 여기서 보지 않아 한글 이름 검색이 늘 0건이었다.
      var hay = data[i].t + " " + (data[i].a || "");
      if (hay.toLowerCase().indexOf(lq) >= 0) hits.push(data[i]);
    }
    if (!hits.length) {
      box.innerHTML = '<p class="ss_empty">‘' + esc(q) + '’ 에 대한 결과가 없습니다.</p>';
      box.hidden = false;
      return;
    }
    var html = '<p class="ss_count">' + hits.length +
               (hits.length === 40 ? "개 이상" : "개") + ' 찾음</p><ul class="ss_list">';
    for (var j = 0; j < hits.length; j++) {
      var h = hits[j];
      html += '<li><a href="' + BASE + h.p + '">' +
              '<span class="ss_where">' + esc(h.s) + " › " + esc(h.pt) + "</span>" +
              '<span class="ss_txt">' + mark(h.t, lq) + "</span></a></li>";
    }
    box.innerHTML = html + "</ul>";
    box.hidden = false;
  }

  var timer;
  input.addEventListener("input", function () {
    clearTimeout(timer);
    // 색인이 늦게 도착해도 그릴 때 입력칸을 다시 읽어, 화면과 검색어가 어긋나지 않게 한다
    timer = setTimeout(function () {
      load().then(function () { render(input.value.trim()); });
    }, 120);
  });

  input.addEventListener("keydown", function (e) {
    if (e.key === "Escape") { input.value = ""; box.hidden = true; input.blur(); }
  });

  // '/' 로 검색창에 바로 간다 (입력 중일 때는 방해하지 않는다)
  document.addEventListener("keydown", function (e) {
    if (e.key !== "/" || e.ctrlKey || e.metaKey) return;
    var t = e.target.tagName;
    if (t === "INPUT" || t === "TEXTAREA" || e.target.isContentEditable) return;
    e.preventDefault();
    input.focus();
  });

  document.addEventListener("click", function (e) {
    if (!box.hidden && !box.contains(e.target) && e.target !== input) box.hidden = true;
  });
})();
