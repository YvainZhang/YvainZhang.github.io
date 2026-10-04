(function () {
  "use strict";
  async function renderDiagrams() {
    if (!window.mermaid) return;
    mermaid.initialize({ startOnLoad: false, securityLevel: "strict", theme: "neutral" });
    var nodes = document.querySelectorAll(".platform-mermaid");
    for (var i = 0; i < nodes.length; i++) {
      var node = nodes[i];
      var source = node.textContent;
      try {
        await mermaid.parse(source);
        var result = await mermaid.render("platform-diagram-" + i, source);
        node.innerHTML = result.svg;
        node.setAttribute("data-processed", "true");
        if (result.bindFunctions) result.bindFunctions(node);
      } catch (error) {
        node.textContent = source;
        node.setAttribute("data-render-error", "true");
        console.error("Platform diagram " + (i + 1) + " failed", error);
      }
    }
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", renderDiagrams);
  } else {
    renderDiagrams();
  }
})();
