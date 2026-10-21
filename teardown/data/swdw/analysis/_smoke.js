
const fs = require('fs');
const els = {};
function mk(id){
  return {
    id: id, _h: '', _t: '',
    set innerHTML(v){ this._h = String(v); }, get innerHTML(){ return this._h; },
    set textContent(v){ this._t = String(v); }, get textContent(){ return this._t; },
    classList:{ _s:new Set(), add(c){this._s.add(c);}, remove(c){this._s.delete(c);}, contains(c){return this._s.has(c);} },
    querySelector(sel){ if(!this._q) this._q={}; return this._q[sel] || (this._q[sel]=mk(id+sel)); },
    getBoundingClientRect(){ return {top:100}; }
  };
}
let qs = 0;
global.document = {
  getElementById(id){ return els[id] || (els[id] = mk(id)); },
  querySelectorAll(sel){ qs++; return [1,2,3,4,5,6,7].map(i => mk('c'+i)); }
};
global.window = { pageYOffset: 0, scrollTo(){} };
global.setTimeout = function(){};

try { eval(fs.readFileSync(process.argv[2], 'utf8')); }
catch(e){ console.log('RUNTIME ERROR:', e.message); process.exit(1); }

const g = els['wgrid'].innerHTML;
const cnt = s => (g.match(new RegExp(s,'g'))||[]).length;
console.log('title  :', els['t-title'].textContent);
console.log('cards  :', cnt('class="wcard"'));
console.log('details:', cnt('class="wdetail"'));
console.log('badges :', JSON.stringify((g.match(/b-(pass|fail|destroy|pending)/g)||[])
              .reduce((a,k)=>(a[k]=(a[k]||0)+1,a),{})));
console.log('stats  :', els['stats'].innerHTML.replace(/<[^>]+>/g,'|').replace(/\|+/g,'|').trim());
console.log('strip  :', (els['strip'].innerHTML.match(/<i /g)||[]).length, 'segments');
console.log('rules  :', (els['m-rules'].innerHTML.match(/<tr>/g)||[]).length, 'rows');
console.log('ruleTL :', (els['rule-tl'].innerHTML.match(/tl-item/g)||[]).length);
console.log('yuTL   :', (els['yu-tl'].innerHTML.match(/tl-item/g)||[]).length);
console.log('chap   :', (els['chapters'].innerHTML.match(/<details>/g)||[]).length,
            'groups /', (els['chapters'].innerHTML.match(/class="ci"/g)||[]).length, 'items');
console.log('death  :', cnt('死亡清单'), 'table(s)');
console.log('theme  :', els['theme'].textContent.slice(0,36) + '...');
console.log('clicks-bound:', qs);
console.log('OK');
