/* 홈 사이트 검색.
 * GitHub Pages 는 정적이라 검색 서버가 없다. 빌드 때 만들어 둔
 * assets/search-index.json 을 첫 입력 시 한 번만 받아 브라우저에서 찾는다.
 * 색인은 tools/build_search_index.py 가 생성한다. */
(function () {
  var input = document.getElementById("ssq");
  var box = document.getElementById("ssResults");
  if (!input || !box) return;

  var data = null, loading = false;

  function load() {
    if (data || loading) return Promise.resolve(data);
    loading = true;
    return fetch("assets/search-index.json")
      .then(function (r) { return r.json(); })
      .then(function (j) { data = j; loading = false; return j; })
      .catch(function () { loading = false; return null; });
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
      if (data[i].t.toLowerCase().indexOf(lq) >= 0) hits.push(data[i]);
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
      html += '<li><a href="' + h.p + '">' +
              '<span class="ss_where">' + esc(h.s) + " › " + esc(h.pt) + "</span>" +
              '<span class="ss_txt">' + mark(h.t, lq) + "</span></a></li>";
    }
    box.innerHTML = html + "</ul>";
    box.hidden = false;
  }

  var timer;
  input.addEventListener("input", function () {
    var q = input.value.trim();
    clearTimeout(timer);
    timer = setTimeout(function () { load().then(function () { render(q); }); }, 120);
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
