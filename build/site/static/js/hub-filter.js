/* 혼살림 — 시나리오 허브 클라이언트 필터 (점진적 향상; JS 없어도 전체 노출).
   카드의 data-persona / data-budget / data-season 와 체크박스를 매칭. */
(function () {
  "use strict";
  var cards = Array.prototype.slice.call(document.querySelectorAll(".hub-cards .s-card"));
  var checks = Array.prototype.slice.call(document.querySelectorAll(".chk[data-filter]"));
  var countEl = document.querySelector("[data-result-count]");
  var emptyEl = document.querySelector("[data-empty]");
  var clearBtn = document.querySelector("[data-clear]");
  if (!cards.length || !checks.length) return;

  function activeValues(group) {
    return checks
      .filter(function (c) { return c.dataset.group === group && c.classList.contains("on"); })
      .map(function (c) { return c.dataset.value; });
  }

  function apply() {
    var ps = activeValues("persona");
    var bs = activeValues("budget");
    var ss = activeValues("season");
    var shown = 0;
    cards.forEach(function (card) {
      var ok =
        (ps.length === 0 || ps.indexOf(card.dataset.persona) !== -1) &&
        (bs.length === 0 || bs.indexOf(card.dataset.budget) !== -1) &&
        (ss.length === 0 || ss.indexOf(card.dataset.season) !== -1);
      card.style.display = ok ? "" : "none";
      if (ok) shown++;
    });
    if (countEl) countEl.textContent = shown;
    if (emptyEl) emptyEl.style.display = shown ? "none" : "";
  }

  checks.forEach(function (c) {
    c.addEventListener("click", function (e) {
      e.preventDefault();
      c.classList.toggle("on");
      apply();
    });
  });

  if (clearBtn) {
    clearBtn.addEventListener("click", function () {
      checks.forEach(function (c) { c.classList.remove("on"); });
      apply();
    });
  }

  apply();
})();
