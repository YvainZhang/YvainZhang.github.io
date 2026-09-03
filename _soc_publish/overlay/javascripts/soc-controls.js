(function () {
  "use strict";

  function initSocControls() {
    var sidebar = document.querySelector(".md-sidebar--primary .md-sidebar__inner");
    var article = document.querySelector(".md-content__inner");
    if (!sidebar || !article || sidebar.querySelector(".soc-side-tools")) return;

    var topTrack = document.createElement("div");
    topTrack.className = "soc-reading-track";
    topTrack.setAttribute("aria-hidden", "true");
    topTrack.innerHTML = '<span class="soc-reading-bar"></span>';
    document.body.appendChild(topTrack);

    var tools = document.createElement("section");
    tools.className = "soc-side-tools";
    tools.setAttribute("aria-label", "阅读与主题设置");
    tools.innerHTML =
      '<div class="soc-side-tools__head"><span>阅读进度</span><output>0%</output></div>' +
      '<div class="soc-side-progress" role="progressbar" aria-label="当前文章阅读进度" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0"><span></span></div>';
    sidebar.insertBefore(tools, sidebar.firstChild);

    var output = tools.querySelector("output");
    var sideBar = tools.querySelector(".soc-side-progress span");
    var progress = tools.querySelector(".soc-side-progress");
    var pageBar = topTrack.querySelector(".soc-reading-bar");
    var scheduled = false;

    function updateProgress() {
      scheduled = false;
      var articleTop = article.getBoundingClientRect().top + window.scrollY;
      var articleEnd = articleTop + article.offsetHeight;
      var readable = Math.max(1, articleEnd - articleTop - window.innerHeight * 0.55);
      var percent = Math.round((window.scrollY - articleTop + window.innerHeight * 0.18) / readable * 100);
      percent = Math.max(0, Math.min(100, percent));
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
    updateProgress();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initSocControls);
  } else {
    initSocControls();
  }
})();
