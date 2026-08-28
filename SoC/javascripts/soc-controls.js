(function () {
  "use strict";

  function createIcon(path) {
    return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="' + path + '"></path></svg>';
  }

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
      '<div class="soc-side-progress" role="progressbar" aria-label="当前文章阅读进度" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0"><span></span></div>' +
      '<div class="soc-theme-switch" role="group" aria-label="页面主题">' +
        '<button type="button" data-soc-theme="default" aria-pressed="false">' + createIcon("M12 18a6 6 0 1 0 0-12 6 6 0 0 0 0 12m0 4h-1v-3h2v3zm0-17h-1V2h2v3zm10 8h-3v-2h3zM5 13H2v-2h3zm13.36 6.78-2.12-2.12 1.42-1.42 2.12 2.12zM6.34 7.76 4.22 5.64l1.42-1.42 2.12 2.12zm11.32 0-1.42-1.42 2.12-2.12 1.42 1.42zM5.64 19.78l-1.42-1.42 2.12-2.12 1.42 1.42z") + '<span>浅色</span></button>' +
        '<button type="button" data-soc-theme="slate" aria-pressed="false">' + createIcon("M17.75 4.09 15.22 6.03l.91 3.06-2.63-1.77-2.63 1.77.91-3.06-2.53-1.94 3.14-.08L13.5 1l1.11 3.01zm3.5 6.13-1.64 1.25.59 1.98-1.7-1.14-1.7 1.14.59-1.98-1.64-1.25 2.04-.05.71-1.95.71 1.95zM18.97 15l-2.5 1.93.93 3.07-2.57-1.78L12.25 20l.93-3.07-2.5-1.93 3.13-.08L14.83 12l1.02 2.92zM9 4.65A7 7 0 1 0 19.35 15 8.5 8.5 0 1 1 9 4.65") + '<span>深色</span></button>' +
      '</div>';
    sidebar.insertBefore(tools, sidebar.firstChild);

    var output = tools.querySelector("output");
    var sideBar = tools.querySelector(".soc-side-progress span");
    var progress = tools.querySelector(".soc-side-progress");
    var pageBar = topTrack.querySelector(".soc-reading-bar");
    var themeButtons = Array.prototype.slice.call(tools.querySelectorAll("[data-soc-theme]"));
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

    function syncThemeButtons() {
      var scheme = document.body.getAttribute("data-md-color-scheme") || "default";
      themeButtons.forEach(function (button) {
        button.setAttribute("aria-pressed", String(button.getAttribute("data-soc-theme") === scheme));
      });
    }

    themeButtons.forEach(function (button) {
      button.addEventListener("click", function () {
        var scheme = button.getAttribute("data-soc-theme");
        var input = document.querySelector('.md-option[data-md-color-scheme="' + scheme + '"]');
        if (input) input.click();
        window.requestAnimationFrame(syncThemeButtons);
      });
    });

    var themeObserver = new MutationObserver(syncThemeButtons);
    themeObserver.observe(document.body, { attributes: true, attributeFilter: ["data-md-color-scheme"] });
    window.addEventListener("scroll", scheduleProgress, { passive: true });
    window.addEventListener("resize", scheduleProgress);
    syncThemeButtons();
    updateProgress();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initSocControls);
  } else {
    initSocControls();
  }
})();
