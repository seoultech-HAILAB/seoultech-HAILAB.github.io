/* 오른쪽 아래 'HAI Lab 도우미'.
 *
 * 답은 Cloudflare Worker(tools/hai-ask.worker.js)가 만든다. 이 사이트는 정적이라
 * 키를 페이지에 둘 수 없기 때문이다. 아래 주소를 워커 주소로 바꾸면 살아난다.
 * 비워 두면 패널은 열리되 '준비 중'이라고만 답한다 — 껍데기가 말없이 죽어 있는 것보다 낫다. */
const ASK_ENDPOINT = "";   // 예: https://hai-ask.<계정>.workers.dev

(function () {
  var fab = document.getElementById("aiFab");
  var panel = document.getElementById("aiPanel");
  if (!fab || !panel) return;

  var body = panel.querySelector(".ai_body");
  var inputBox = panel.querySelector(".ai_input");
  var closeBtn = panel.querySelector(".ai_x");
  var history = [];
  var busy = false;

  /* 껍데기 시절의 가짜 입력칸을 진짜 입력칸으로 바꾼다 */
  inputBox.innerHTML =
    '<input id="aiText" type="text" maxlength="400" autocomplete="off" placeholder="궁금한 것을 물어보세요">' +
    '<button class="ai_send" aria-label="보내기">&#10148;</button>';
  var field = inputBox.querySelector("#aiText");
  var send = inputBox.querySelector(".ai_send");

  function open(yes) {
    panel.hidden = !yes;
    fab.setAttribute("aria-expanded", String(yes));
    if (yes) field.focus();
  }
  fab.addEventListener("click", function () { open(panel.hidden); });
  closeBtn.addEventListener("click", function () { open(false); });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && !panel.hidden) open(false);
  });

  function bubble(role, text) {
    var p = document.createElement("p");
    p.className = "ai_msg" + (role === "user" ? " is-me" : "");
    p.textContent = text;
    body.appendChild(p);
    body.scrollTop = body.scrollHeight;
    return p;
  }

  function ask(text) {
    if (busy || !text.trim()) return;
    busy = true;
    bubble("user", text);
    history.push({ role: "user", content: text });
    field.value = "";

    var wait = bubble("bot", "…");

    if (!ASK_ENDPOINT) {
      wait.textContent = "도우미는 아직 연결 전입니다. 문의는 kwseo@seoultech.ac.kr 로 부탁드립니다.";
      busy = false;
      return;
    }

    fetch(ASK_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages: history.slice(-12) }),
    })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        var a = d.answer || d.error || "답을 만들지 못했습니다.";
        wait.textContent = a;
        if (d.answer) history.push({ role: "assistant", content: d.answer });
      })
      .catch(function () {
        wait.textContent = "연결이 되지 않았습니다. 잠시 후 다시 시도해 주세요.";
      })
      .finally(function () { busy = false; });
  }

  send.addEventListener("click", function () { ask(field.value); });
  field.addEventListener("keydown", function (e) {
    if (e.key === "Enter") { e.preventDefault(); ask(field.value); }
  });

  /* 예시 질문을 누르면 그대로 보낸다 */
  panel.querySelectorAll(".ai_sugg span").forEach(function (s) {
    s.setAttribute("role", "button");
    s.setAttribute("tabindex", "0");
    s.addEventListener("click", function () { ask(s.textContent.trim()); });
    s.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); ask(s.textContent.trim()); }
    });
  });
})();
