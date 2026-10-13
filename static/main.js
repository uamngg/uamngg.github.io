(function () {
  var top = document.getElementById('top');
  function onScroll() { top.classList.toggle('solid', window.scrollY > 40); }
  onScroll();
  window.addEventListener('scroll', onScroll, { passive: true });

  // reveal on scroll
  var els = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
      });
    }, { threshold: 0.12 });
    els.forEach(function (el, i) {
      el.style.transitionDelay = (i % 3) * 70 + 'ms';
      io.observe(el);
    });
  } else {
    els.forEach(function (el) { el.classList.add('in'); });
  }

  // work filter
  var bar = document.querySelector('.filters');
  if (bar) {
    bar.addEventListener('click', function (e) {
      var t = e.target.closest('button'); if (!t) return;
      bar.querySelectorAll('button').forEach(function (b) { b.classList.toggle('on', b === t); });
      document.querySelectorAll('#grid .item').forEach(function (c) {
        var show = !t.dataset.cat || c.dataset.cat === t.dataset.cat;
        c.classList.toggle('gone', !show);
      });
    });
  }

  // play clip previews on hover
  document.querySelectorAll('.item video').forEach(function (v) {
    var card = v.closest('.item');
    card.addEventListener('mouseenter', function () { v.play(); });
    card.addEventListener('mouseleave', function () { v.pause(); });
  });

  // fade out when leaving to another page
  document.addEventListener('click', function (e) {
    var a = e.target.closest('a');
    if (!a || a.target || e.metaKey || e.ctrlKey || e.shiftKey) return;
    var u = new URL(a.href, location.href);
    if (u.origin !== location.origin || u.pathname === location.pathname) return;
    e.preventDefault();
    document.body.classList.add('leaving');
    setTimeout(function () { location.href = a.href; }, 180);
  });
  window.addEventListener('pageshow', function () { document.body.classList.remove('leaving'); });
})();
