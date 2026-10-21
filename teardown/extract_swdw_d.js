const vm = require('vm');
const fs = require('fs');

const srcPath = 'D:/2026/WB项目/拆书/data/swdw/analysis/_t.js';
const outDir = 'D:/2026/WB项目/拆书/data/swdw/';
const src = fs.readFileSync(srcPath, 'utf8');

// 用 Proxy 做一个能吸收一切 set/get/调用的 document 桩，让渲染器代码无错跑完
const stub = new Proxy(function () {}, {
  get(t, p) {
    if (p === 'innerHTML' || p === 'textContent' || p === 'value') return '';
    if (p === Symbol.toPrimitive) return () => '';
    return stub;
  },
  set() { return true; },
  apply() { return stub; },
});
const documentStub = {
  getElementById: () => stub,
  querySelector: () => stub,
  querySelectorAll: () => [],
  createElement: () => stub,
  body: stub,
};
const sandbox = {
  document: documentStub,
  window: { pageYOffset: 0, scrollTo() {} },
  console,
  setTimeout: () => {},
  navigator: { userAgent: 'node' },
};
vm.createContext(sandbox);

// 把 `const D =` 改成全局赋值，便于取出
const code = src.replace('const D =', 'globalThis.D =');
vm.runInContext(code, sandbox);
const D = sandbox.D;

if (!D || !D.meta) {
  console.error('FAIL: D 未取到');
  process.exit(1);
}

fs.writeFileSync(outDir + 'data.json', JSON.stringify(D, null, 2), 'utf8');

// 概要
const report = {
  title: D.meta.title,
  author: D.meta.author,
  total_chapters: D.meta.total_chapters,
  worlds: (D.worlds || []).map(w => ({
    index: w.index, name: w.name, full_title: w.full_title,
    chapter_start: w.chapter_start, chapter_end: w.chapter_end,
    characters: (w.characters || []).length,
    plot_stages: (w.plot || []).length,
    verdict: w.verdict ? w.verdict.world : null,
    has_deaths: Array.isArray(w.deaths) ? w.deaths.length : 0,
  })),
  chapter_index_len: (D.chapter_index || []).length,
  rule_evolution: (D.rule_evolution || []).length,
  yu_arc: (D.yu_arc || []).length,
};
console.log(JSON.stringify(report, null, 2));
console.log('\nOK ->', outDir + 'data.json', fs.statSync(outDir + 'data.json').size, 'bytes');
