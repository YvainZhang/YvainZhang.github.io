(function () {
  "use strict";

  function initRtosControls() {
    var sidebar = document.querySelector(".md-sidebar--primary .md-sidebar__inner");
    var article = document.querySelector(".md-content__inner");
    if (!sidebar || !article || sidebar.querySelector(".rtos-side-tools")) return;

    var topTrack = document.createElement("div");
    topTrack.className = "rtos-reading-track";
    topTrack.setAttribute("aria-hidden", "true");
    topTrack.innerHTML = '<span class="rtos-reading-bar"></span>';
    document.body.appendChild(topTrack);

    var tools = document.createElement("section");
    tools.className = "rtos-side-tools";
    tools.setAttribute("aria-label", "阅读进度");
    tools.innerHTML =
      '<div class="rtos-side-tools__head"><span>阅读进度</span><output>0%</output></div>' +
      '<div class="rtos-side-progress" role="progressbar" aria-label="当前文章阅读进度" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0"><span></span></div>';
    sidebar.insertBefore(tools, sidebar.firstChild);

    var output = tools.querySelector("output");
    var sideBar = tools.querySelector(".rtos-side-progress span");
    var progress = tools.querySelector(".rtos-side-progress");
    var pageBar = topTrack.querySelector(".rtos-reading-bar");
    var scheduled = false;

    function updateProgress() {
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
      sideBar.style.width = percent + "%";
      pageBar.style.width = percent + "%";
      progress.setAttribute("aria-valuenow", String(percent));
    }

    function scheduleProgress() {
      if (!scheduled) {
        scheduled = true;
        window.requestAnimationFrame(updateProgress);
      }
    }

    window.addEventListener("scroll", scheduleProgress, { passive: true });
    window.addEventListener("resize", scheduleProgress);
    window.addEventListener("load", scheduleProgress);
    // Images, Mermaid and math can resize the article after initial rendering.
    if (typeof ResizeObserver !== "undefined") {
      var observer = new ResizeObserver(scheduleProgress);
      observer.observe(article);
      observer.observe(document.body);
    }
    updateProgress();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initRtosControls);
  } else {
    initRtosControls();
  }
})();
