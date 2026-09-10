(function () {
  "use strict";
  async function renderDiagrams() {
    if (!window.mermaid) return;
    mermaid.initialize({ startOnLoad: false, securityLevel: "strict", theme: "neutral" });
    var nodes = document.querySelectorAll(".rtos-mermaid");
    for (var i = 0; i < nodes.length; i++) {
      var node = nodes[i];
      // Read the original code text directly: do not round-trip through innerHTML.
      var source = node.textContent;
      try {
        await mermaid.parse(source);
        var result = await mermaid.render("rtos-diagram-" + i, source);
        node.innerHTML = result.svg;
        node.classList.add("mermaid");
        node.setAttribute("data-processed", "true");
        if (result.bindFunctions) result.bindFunctions(node);
      } catch (error) {
        node.textContent = source;
        console.error("Mermaid diagram " + (i + 1) + " failed", error);
      }
    }
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", renderDiagrams);
  } else {
    renderDiagrams();
  }
})();
