/* category.js — 카테고리 페이지 '전체 제품' 정렬·티어 필터 (세션 #19).
   서버 렌더 카드(.card[data-price|data-disc|data-tier|data-idx])를 클라이언트에서
   재정렬·표시/숨김만 한다(데이터 조작·점수 매김 없음 — 가격·할인·추천 순서만).
   진행 향상: JS가 없으면 서버 기본(추천순·전체)이 그대로 보인다. */
(function () {
  "use strict";

  var grid = document.getElementById("catGrid");
  if (!grid) return;

  var sortBar = document.getElementById("catSort");
  var tierBar = document.getElementById("catTier");
  var countEl = document.getElementById("catCount");
  var cards = Array.prototype.slice.call(grid.querySelectorAll(".card"));
  if (!cards.length) return;

  var state = { sort: "reco", tier: "all" };
  var SORT_LABEL = { reco: "추천순", price: "낮은 가격순", disc: "할인율 높은순" };

  function num(el, attr) {
    return parseInt(el.getAttribute(attr), 10) || 0;
  }

  function apply() {
    // 1) 정렬 — 추천순(원래 순서)·가격 오름차순·할인율 내림차순
    var ordered = cards.slice();
    if (state.sort === "price") {
      ordered.sort(function (a, b) {
        return num(a, "data-price") - num(b, "data-price");
      });
    } else if (state.sort === "disc") {
      ordered.sort(function (a, b) {
        return num(b, "data-disc") - num(a, "data-disc");
      });
    } else {
      ordered.sort(function (a, b) {
        return num(a, "data-idx") - num(b, "data-idx");
      });
    }
    ordered.forEach(function (c) {
      grid.appendChild(c); // DOM 순서 재배치
    });

    // 2) 티어 필터 + 표시 개수 갱신
    var shown = 0;
    ordered.forEach(function (c) {
      var ok = state.tier === "all" || c.getAttribute("data-tier") === state.tier;
      c.style.display = ok ? "" : "none";
      if (ok) shown++;
    });
    if (countEl) {
      countEl.innerHTML = "전체 <b>" + shown + "</b>개 · " + SORT_LABEL[state.sort];
    }
  }

  function bind(bar, key, attr, itemClass) {
    if (!bar) return;
    bar.addEventListener("click", function (e) {
      var target = e.target.closest ? e.target.closest("[" + attr + "]") : null;
      if (!target || !bar.contains(target)) return;
      state[key] = target.getAttribute(attr);
      var items = bar.querySelectorAll("." + itemClass);
      for (var i = 0; i < items.length; i++) items[i].classList.remove("on");
      target.classList.add("on");
      apply();
    });
  }

  bind(sortBar, "sort", "data-sort", "sort");
  bind(tierBar, "tier", "data-tier", "chip");
})();
