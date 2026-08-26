/* Research > Demos 의 자기노출 챗봇 시연.
 *
 * 답은 도우미와 같은 워커가 만든다 (tools/hai-ask.worker.js 의 /demo 경로).
 * 키를 페이지에 둘 수 없어서다. 프롬프트만 다르고 나머지 구조는 도우미와 같다. */
(function () {
  var ENDPOINT = "https://hai-ask.rubying1318.workers.dev/demo";

  var body = document.getElementById("dcBody");
  var form = document.getElementById("dcForm");
  var field = document.getElementById("dcText");
  var chips = document.getElementById("dcChips");
  if (!body || !form || !field) return;

  var history = [];
  var busy = false;

  function bubble(who, text) {
    var p = document.createElement("p");
    p.className = "dc_msg dc_" + who;
    p.textContent = text;
    body.appendChild(p);
    body.scrollTop = body.scrollHeight;
    return p;
  }

  function send(text) {
    text = (text || "").trim();
    if (busy || !text) return;
    busy = true;
    field.value = "";
    if (chips) chips.hidden = true;      // 한 번 말을 걸면 예시는 치운다

    bubble("me", text);
    history.push({ role: "user", content: text });

    var wait = bubble("bot", "…");
    wait.classList.add("is-wait");

    fetch(ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages: history.slice(-12) }),
    })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        var a = d.answer || "지금은 답을 만들지 못했어요. 잠시 후 다시 말 걸어 주세요.";
        wait.textContent = a;
        wait.classList.remove("is-wait");
        if (d.answer) history.push({ role: "assistant", content: d.answer });
      })
      .catch(function () {
        wait.textContent = "연결이 되지 않았어요. 잠시 후 다시 시도해 주세요.";
        wait.classList.remove("is-wait");
      })
      .finally(function () { busy = false; field.focus(); });
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    send(field.value);
  });

  if (chips) {
    chips.addEventListener("click", function (e) {
      var b = e.target.closest("button");
      if (b) send(b.textContent);
    });
  }
})();
