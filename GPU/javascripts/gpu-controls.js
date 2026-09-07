(function () {
  "use strict";

  function initGpuControls() {
    var sidebar = document.querySelector(".md-sidebar--primary .md-sidebar__inner");
    var article = document.querySelector(".md-content__inner");
    if (!sidebar || !article || sidebar.querySelector(".gpu-side-tools")) return;

    var topTrack = document.createElement("div");
    topTrack.className = "gpu-reading-track";
    topTrack.setAttribute("aria-hidden", "true");
    topTrack.innerHTML = '<span class="gpu-reading-bar"></span>';
    document.body.appendChild(topTrack);

    var tools = document.createElement("section");
    tools.className = "gpu-side-tools";
    tools.setAttribute("aria-label", "阅读进度");
    tools.innerHTML =
      '<div class="gpu-side-tools__head"><span>阅读进度</span><output>0%</output></div>' +
      '<div class="gpu-side-progress" role="progressbar" aria-label="当前文章阅读进度" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0"><span></span></div>';
    sidebar.insertBefore(tools, sidebar.firstChild);

    var output = tools.querySelector("output");
    var sideBar = tools.querySelector(".gpu-side-progress span");
    var progress = tools.querySelector(".gpu-side-progress");
    var pageBar = topTrack.querySelector(".gpu-reading-bar");
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
    document.addEventListener("DOMContentLoaded", initGpuControls);
  } else {
    initGpuControls();
  }
})();
