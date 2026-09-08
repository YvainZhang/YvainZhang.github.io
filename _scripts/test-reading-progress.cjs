// Run the actual atlas scripts against controlled layout and browser events.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const { test } = require('node:test');
const path = require('node:path');

const scripts = [
  'GPU/javascripts/gpu-controls.js',
  'NPU/javascripts/npu-controls.js',
  'WiFi/javascripts/wifi-controls.js',
  'SoC/javascripts/soc-controls.js',
  '_soc_publish/overlay/javascripts/soc-controls.js',
  'Audio/javascripts/audio-controls.js',
];

function mount(file, { top = 200, height = 2000, viewport = 800, total = 2300, scroll = 0 } = {}) {
  const nodes = [];
  function element() {
    const children = new Map();
    const node = { style: {}, attrs: {}, textContent: '',
      setAttribute(k, v) { this.attrs[k] = v; },
      querySelector(selector) {
        if (!children.has(selector)) children.set(selector, element());
        return children.get(selector);
      },
    };
    nodes.push(node);
    return node;
  }
  const events = {};
  const frames = [];
  const observers = [];
  const window = { scrollY: scroll, innerHeight: viewport,
    addEventListener(name, fn) { events[name] = fn; },
    requestAnimationFrame(fn) { frames.push(fn); },
  };
  const article = { offsetHeight: height,
    getBoundingClientRect() { return { top: top - window.scrollY }; },
  };
  const body = { appendChild() {} };
  const root = { scrollHeight: total };
  const sidebar = { querySelector() { return null; }, insertBefore() {} };
  const document = { readyState: 'complete', body, scrollingElement: root,
    documentElement: root, createElement: element,
    querySelector(selector) { return selector === '.md-content__inner' ? article : sidebar; },
  };
  class ResizeObserver {
    constructor(fn) { this.callback = fn; this.targets = []; observers.push(this); }
    observe(target) { this.targets.push(target); }
  }
  vm.runInNewContext(fs.readFileSync(path.join(__dirname, '..', file), 'utf8'),
    { window, document, ResizeObserver });
  function percent() {
    const output = nodes.find(n => /^\d+%$/.test(n.textContent));
    const value = Number.parseInt(output.textContent, 10);
    for (const node of nodes) {
      if ('aria-valuenow' in node.attrs) assert.equal(node.attrs['aria-valuenow'], String(value));
      if ('value' in node) assert.equal(node.value, value);
      if ('width' in node.style) assert.equal(node.style.width, value + '%');
    }
    return value;
  }
  function flush() { while (frames.length) frames.shift()(); }
  return { window, article, root, observers, body, percent, flush,
    fire(name) { events[name](); flush(); } };
}

for (const file of scripts) {
  test(file + ': progress follows reachable article end', () => {
    const page = mount(file);
    assert.equal(page.percent(), 0);
    let previous = 0;
    for (let scroll = 100; scroll <= 1400; scroll += 100) {
      page.window.scrollY = scroll;
      page.fire('scroll');
      assert.ok(page.percent() >= previous);
      previous = page.percent();
    }
    assert.equal(page.percent(), 100); // Article bottom visible before page bottom.
  });
  test(file + ': short, fractional, clamped and large-footer layouts', () => {
    assert.equal(mount(file, { height: 300, total: 800 }).percent(), 100);
    assert.equal(mount(file, { height: 300, total: 4000 }).percent(), 100);
    assert.equal(mount(file, { scroll: 1399.5 }).percent(), 100);
    assert.equal(mount(file, { scroll: -20 }).percent(), 0);
    assert.equal(mount(file, { total: 2100, scroll: 1300 }).percent(), 100);
    assert.equal(mount(file, { total: 4000, scroll: 1400 }).percent(), 100);
  });
  test(file + ': late content, load and viewport resize update all indicators', () => {
    const page = mount(file, { height: 300, total: 800 });
    assert.equal(page.percent(), 100);
    page.article.offsetHeight = 2000;
    page.root.scrollHeight = 2300;
    assert.ok(page.observers[0].targets.includes(page.article));
    assert.ok(page.observers[0].targets.includes(page.body));
    page.observers[0].callback();
    page.flush();
    assert.equal(page.percent(), 0);
    page.window.scrollY = 1400;
    page.fire('load');
    assert.equal(page.percent(), 100);
    page.window.innerHeight = 600;
    page.fire('resize');
    assert.ok(page.percent() < 100);
  });
}

test('SoC overlay matches published snapshot', () => {
  assert.equal(fs.readFileSync(path.join(__dirname, '..', scripts[3]), 'utf8'),
    fs.readFileSync(path.join(__dirname, '..', scripts[4]), 'utf8'));
});
