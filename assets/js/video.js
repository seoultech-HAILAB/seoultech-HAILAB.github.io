/* 영상은 사이트 안에서 튼다.
 * data-yt="<id>" 가 붙은 링크를 가로채 유튜브 임베드를 겹쳐 띄운다.
 * 스크립트가 죽어도 href 가 남아 있으므로 유튜브로 가긴 간다. */
(function () {
  var box = null, lastFocus = null;

  function close() {
    if (!box) return;
    box.remove(); box = null;
    document.body.style.overflow = "";
    if (lastFocus) lastFocus.focus();
  }

  function open(id, title) {
    close();
    lastFocus = document.activeElement;
    box = document.createElement("div");
    box.className = "vmodal";
    box.setAttribute("role", "dialog");
    box.setAttribute("aria-modal", "true");
    box.setAttribute("aria-label", title || "영상");
    box.innerHTML =
      '<div class="vm_back"></div>' +
      '<div class="vm_panel">' +
        '<button class="vm_x" aria-label="닫기">&times;</button>' +
        '<div class="vm_frame"><iframe src="https://www.youtube.com/embed/' + id +
          '?autoplay=1&rel=0" title="' + (title || "").replace(/"/g, "&quot;") +
          '" allow="accelerometer; autoplay; clipboard-write; encrypted-media; picture-in-picture" ' +
          'allowfullscreen></iframe></div>' +
        (title ? '<p class="vm_tit">' + title + "</p>" : "") +
      "</div>";
    document.body.appendChild(box);
    document.body.style.overflow = "hidden";
    box.querySelector(".vm_x").focus();
    box.querySelector(".vm_back").addEventListener("click", close);
    box.querySelector(".vm_x").addEventListener("click", close);
  }

  document.addEventListener("click", function (e) {
    var a = e.target.closest("[data-yt]");
    if (!a) return;
    e.preventDefault();
    var t = a.querySelector(".mvp_tit, .bf_tit, .vid_tit, h4");
    open(a.getAttribute("data-yt"), t ? t.textContent.trim() : "");
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") close();
  });
})();
