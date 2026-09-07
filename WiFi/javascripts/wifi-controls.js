(function () {
  "use strict";

  function initReadingProgress() {
    var sidebar = document.querySelector(".md-sidebar--primary .md-sidebar__inner");
    var article = document.querySelector(".md-content__inner");
    if (!sidebar || !article || sidebar.querySelector(".wifi-side-tools")) return;

    var track = document.createElement("div");
    track.className = "wifi-reading-track";
    track.setAttribute("aria-hidden", "true");
    track.innerHTML = '<span class="wifi-reading-bar"></span>';
    document.body.appendChild(track);

    var tools = document.createElement("section");
    tools.className = "wifi-side-tools";
    tools.setAttribute("aria-label", "阅读进度");
    tools.innerHTML = '<div><span>阅读进度</span><output>0%</output></div><progress max="100" value="0">0%</progress>';
    sidebar.insertBefore(tools, sidebar.firstChild);

    var output = tools.querySelector("output");
    var progress = tools.querySelector("progress");
    var bar = track.querySelector("span");
    var scheduled = false;

    function update() {
      scheduled = false;
      var scrollTop = Math.max(0, window.scrollY);
      var viewport = window.innerHeight;
      var articleTop = article.getBoundingClientRect().top + window.scrollY;
      var articleEnd = articleTop + article.offsetHeight;
      var root = document.scrollingElement || document.documentElement;
      var maxScroll = Math.max(0, root.scrollHeight - viewport);
      var start = Math.max(0, articleTop - viewport * 0.18);
      // Complete when the article bottom is visible, or the page cannot scroll further.
      var end = Math.max(0, Math.min(articleEnd - viewport, maxScroll));
      var percent = scrollTop >= end - 1 ? 100 :
        Math.max(0, Math.min(99, Math.floor((scrollTop - start) / Math.max(1, end - start) * 100)));
      output.textContent = percent + "%";
      progress.value = percent;
      progress.textContent = percent + "%";
      bar.style.width = percent + "%";
    }

    function schedule() {
      if (!scheduled) {
        scheduled = true;
        window.requestAnimationFrame(update);
      }
    }

    window.addEventListener("scroll", schedule, { passive: true });
    window.addEventListener("resize", schedule);
    window.addEventListener("load", schedule);
    // Images, Mermaid and math can resize the article after initial rendering.
    if (typeof ResizeObserver !== "undefined") {
      var observer = new ResizeObserver(schedule);
      observer.observe(article);
      observer.observe(document.body);
    }
    update();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initReadingProgress);
  else initReadingProgress();
})();
