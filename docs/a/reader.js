// 読んだ位置を覚える。作品と話ごとに別の鍵なので、増えても混ざらない。
(function () {
  var root = document.getElementById('pages');
  if (!root) return;
  var KEY = 'yomi.' + root.dataset.key;
  var TOTAL = Number(root.dataset.total);
  var cur = document.getElementById('cur');
  var rail = document.getElementById('rail');
  var shown = 0;

  function mark(n) {
    if (n === shown) return;
    shown = n;
    if (cur) cur.textContent = String(n).padStart(2, '0');
    if (rail) rail.style.width = (n / TOTAL * 100) + '%';
    try { localStorage.setItem(KEY, String(n)); } catch (e) {}
  }

  var io = new IntersectionObserver(function (es) {
    // 画面の中で一番上にある見えているページを「今のページ」とする
    var best = null;
    es.forEach(function (e) {
      if (!e.isIntersecting) return;
      if (!best || e.boundingClientRect.top < best.boundingClientRect.top) best = e;
    });
    if (best) mark(Number(best.target.dataset.n));
  }, { rootMargin: '-45% 0px -45% 0px' });
  Array.prototype.forEach.call(root.children, function (f) { io.observe(f); });

  // localStorage は private window などで読めないことがある。
  // 読めなくてもページが普通に成立するようにしておく。
  var saved = 0;
  try { saved = Number(localStorage.getItem(KEY)) || 0; } catch (e) {}
  if (saved > 1 && saved <= TOTAL) {
    var bar = document.getElementById('resumeBar');
    var btn = document.getElementById('resumeBtn');
    btn.textContent = String(saved).padStart(2, '0') + 'ページ目から続ける';
    bar.hidden = false;
    btn.addEventListener('click', function () {
      var t = document.getElementById('p' + String(saved).padStart(2, '0'));
      if (t) t.scrollIntoView({ block: 'start' });
      bar.hidden = true;
    });
    window.addEventListener('scroll', function once() {
      bar.hidden = true;
      window.removeEventListener('scroll', once);
    }, { passive: true });
  }
})();
