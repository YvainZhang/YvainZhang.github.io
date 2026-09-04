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
      var top = article.getBoundingClientRect().top + window.scrollY;
      var readable = Math.max(1, article.offsetHeight - window.innerHeight * 0.55);
      var percent = Math.round((window.scrollY - top + window.innerHeight * 0.18) / readable * 100);
      percent = Math.max(0, Math.min(100, percent));
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
    update();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initReadingProgress);
  else initReadingProgress();
})();
