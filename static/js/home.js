/* home.js — 홈 기획전 배너 캐러셀 (세션 #20).
   서버가 첫 슬라이드에 .on을 부여 → JS 없으면 첫 배너만 보인다(진행 향상).
   슬라이드 2개 이상일 때만 자동 회전(5초) + 점(dot) 네비 활성화. */
(function () {
  "use strict";

  var promo = document.getElementById("promo");
  if (!promo) return;

  var slides = Array.prototype.slice.call(promo.querySelectorAll(".promo-slide"));
  var dots = Array.prototype.slice.call(promo.querySelectorAll(".promo-dot"));
  if (slides.length < 2) return; // 1장이면 회전 불필요

  var idx = 0;
  var timer = null;

  function show(n) {
    idx = (n + slides.length) % slides.length;
    slides.forEach(function (s, k) {
      s.classList.toggle("on", k === idx);
    });
    dots.forEach(function (d, k) {
      d.classList.toggle("on", k === idx);
    });
  }

  function restart() {
    if (timer) clearInterval(timer);
    timer = setInterval(function () {
      show(idx + 1);
    }, 5000);
  }

  dots.forEach(function (d) {
    d.addEventListener("click", function (e) {
      e.preventDefault();
      show(parseInt(d.getAttribute("data-i"), 10) || 0);
      restart();
    });
  });

  // 탭이 안 보일 때 회전 정지(리소스 절약)
  document.addEventListener("visibilitychange", function () {
    if (document.hidden) {
      if (timer) clearInterval(timer);
    } else {
      restart();
    }
  });

  restart();
})();
