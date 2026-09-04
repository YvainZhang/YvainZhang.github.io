---
title: Wi-Fi 系统知识库
hide:
  - toc
---

<section class="wifi-home-hero">
  <p class="wifi-home-kicker"><span></span> Technology / System Collection 02</p>
  <h1>Wi-Fi System Atlas</h1>
  <p class="wifi-home-lead">从应用发出一个数据包开始，沿着 Linux 网络栈、Host Driver、USB / SDIO / PCIe、Firmware、MAC 与 PHY，一直追到空口；再沿事件、确认和错误恢复路径返回系统。</p>
  <div class="wifi-home-stats">
    <span><strong>12</strong>核心模块</span>
    <span><strong>40</strong>篇核心指南</span>
    <span><strong>4</strong>个系统案例</span>
    <span><strong>4</strong>个实验</span>
  </div>
</section>

<section class="wifi-home-section">
  <div class="wifi-home-head"><p>Packet Path / 01</p><h2>先跟随一个数据包，穿过完整的 Wi-Fi 系统。</h2></div>
  <div class="wifi-path" aria-label="Wi-Fi 端到端数据路径">
    <a href="04-Linux-Stack/">APP<br>TCP/IP</a><i>→</i><a href="05-Driver-Firmware/">HOST<br>DRIVER</a><i>→</i><a href="06-Bus-Data-Path/">USB / SDIO<br>PCIe</a><i>→</i><a href="05-Driver-Firmware/">FIRMWARE</a><i>→</i><a href="02-80211-MAC/">MAC<br>PHY</a><i>→</i><a href="02-80211-MAC/">AIR</a>
  </div>
</section>

<section class="wifi-home-section">
  <div class="wifi-home-head"><p>Reading Routes / 02</p><h2>按问题选择路线，不必从协议第一页开始读。</h2></div>
  <div class="wifi-route-grid">
    <a href="00-Overview/"><span>Route 01</span><strong>建链与平台适配</strong><p>架构 → 建链安全 → Linux 软件栈 → Driver/Firmware → Android 与并发场景</p></a>
    <a href="00-Overview/"><span>Route 02</span><strong>吞吐、时延与功耗</strong><p>MAC 聚合 → 总线数据通路 → 性能工程 → 低功耗 → 证据链</p></a>
    <a href="00-Overview/"><span>Route 03</span><strong>故障定位与恢复</strong><p>状态机 → 控制事件 → 数据通路 → 抓包与 Trace → Reset/Recovery</p></a>
  </div>
</section>

<section class="wifi-home-section">
  <div class="wifi-home-head"><p>Core Modules / 03</p><h2>十二个模块，从软件数据路径一直深入到芯片与量产。</h2></div>
  <div class="wifi-module-grid">
    <a href="01-System-Architecture/"><span>01</span><strong>Wi-Fi 系统架构</strong><em>Host · Device · Packet</em></a>
    <a href="02-80211-MAC/"><span>02</span><strong>802.11 MAC 与空口</strong><em>Frame · Access · BA</em></a>
    <a href="03-Connection-Security/"><span>03</span><strong>建链与安全</strong><em>Scan · Auth · DHCP</em></a>
    <a href="04-Linux-Stack/"><span>04</span><strong>Linux Wi-Fi 软件栈</strong><em>nl80211 · cfg80211</em></a>
    <a href="05-Driver-Firmware/"><span>05</span><strong>Driver 与 Firmware</strong><em>Command · Event · Reset</em></a>
    <a href="06-Bus-Data-Path/"><span>06</span><strong>总线与数据通路</strong><em>USB · SDIO · PCIe</em></a>
    <a href="07-Performance/"><span>07</span><strong>性能工程</strong><em>Throughput · Latency · CPU</em></a>
    <a href="08-Power/"><span>08</span><strong>低功耗</strong><em>PS · U-APSD · TWT</em></a>
    <a href="09-Scenarios-Integration/"><span>09</span><strong>场景与平台集成</strong><em>P2P · MCC · Android</em></a>
    <a href="10-Debug-Recovery/"><span>10</span><strong>调试与恢复</strong><em>Capture · Trace · Recovery</em></a>
    <a href="11-PHY-RF-Calibration/"><span>11</span><strong>PHY、RF 与校准</strong><em>Vector · EVM · Calibration</em></a>
    <a href="12-Validation-Productization/"><span>12</span><strong>验证、认证与量产</strong><em>UVM · Bring-up · ATE</em></a>
  </div>
</section>

<section class="wifi-home-section">
  <div class="wifi-home-head"><p>Practice / 04</p><h2>把抽象机制放回可观测、可复现的现场。</h2></div>
  <div class="wifi-practice-grid">
    <a href="Case-Studies/"><span>Case Studies</span><strong>四个跨模块案例</strong><p>建链、USB 吞吐、ADDBA 与休眠恢复问题的端到端推演。</p></a>
    <a href="Labs/"><span>Labs</span><strong>四个低门槛实验</strong><p>虚拟无线建链、管理帧抓取、吞吐基线与电源事件观测。</p></a>
    <a href="Glossary/"><span>Glossary</span><strong>术语与边界</strong><p>把协议缩写落回所属层次、状态和可观测证据。</p></a>
  </div>
</section>

!!! note "阅读说明"
    本知识库讲解通用 Wi-Fi 系统机制，不对应特定厂商芯片、Firmware 或私有接口。实际调试应以目标芯片文档、内核版本、认证要求和当地无线法规为准。
