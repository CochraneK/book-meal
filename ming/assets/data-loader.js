/* ===== 按需数据加载器（domain-chunk 版）=====
   设计：boot（data.js）只含元数据，各数据域拆到 assets/data-<name>.js，
   在视图/实体真正被访问时才注入式加载。每个分块文件执行时：
     Object.assign(DATA, {...}) 把数据并入全局 DATA；
     window.__MING_DATA_CHUNKS__[name]=true 标记就绪；
     dispatch ming:data-chunk 通知依赖方。
   本文件不依赖任何外部资源，可在 app.js 之前安全执行（只读取已定义的 DATA）。 */
(function(){
'use strict';
if(typeof DATA==='undefined')return;

const root=document.documentElement;
const ALL_CHUNKS=['characters','locations','events','relations','time','lifespans','graphs','place-chapters','voyages','insight'];
const VIEW_CHUNKS={
  overview:[],distribution:[],
  visuals:['graphs'],
  locations:['locations'],
  map:['locations'],
  characters:['characters'],
  events:['events'],
  relations:['relations'],
  timeline:['time'],
  dynasty:['time'],
  chronicle:['lifespans','characters'],
  insight:['insight']
};
const chunkPromises=Object.create(null);
let fullPromise=null,_fullEventSent=false;
window.__MING_DATA_CHUNKS__=window.__MING_DATA_CHUNKS__||{};

function ready(name){return !!window.__MING_DATA_CHUNKS__[name];}
function readyNames(){return ALL_CHUNKS.filter(ready);}
function syncDataState(reason){
  const names=readyNames();
  root.dataset.mingChunks=names.join(',');
  window.__MING_FULL_DATA_READY=names.length===ALL_CHUNKS.length;
  root.dataset.mingData=window.__MING_FULL_DATA_READY?'full':(names.length?'partial':'boot');
  if(reason)root.dataset.mingDataReason=reason;else delete root.dataset.mingDataReason;
  if(window.__MING_FULL_DATA_READY&&!_fullEventSent){
    _fullEventSent=true;
    document.dispatchEvent(new CustomEvent('ming:data-full'));
  }
}

function uniq(items){return [...new Set((items||[]).filter(x=>ALL_CHUNKS.includes(x)))];}
function entityPlan(kind,id){
  if(kind==='person')return ['characters','insight'];
  if(kind==='place')return ['locations','events','insight'];
  if(kind==='event')return ['events','insight'];
  return ALL_CHUNKS;
}
function resolveEventId(value){
  const raw=String(value||'');
  if(/^event-\d+$/.test(raw))return raw;
  const event=(DATA.events||[]).find(x=>x.id===raw||x.name===raw);
  return event&&event.id||'';
}

function readHash(){
  const raw=String(location.hash||'').replace(/^#/,'');const out={};if(!raw)return out;
  raw.split('&').forEach(part=>{if(!part)return;const i=part.indexOf('=');const k=i<0?part:part.slice(0,i);out[k]=i<0?'':decodeURIComponent(part.slice(i+1));});return out;
}
/* deep link 在 app.js 之前只预载视图/实体真正需要的数据；标准事件 deep link 使用稳定 event-* id。 */
function deepPlan(){
  const p=readHash();
  if(p.person)return entityPlan('person',p.person);
  if(p.event)return entityPlan('event',p.event);
  if(p.place)return entityPlan('place',p.place);
  if(p.view&&p.view!=='overview')return VIEW_CHUNKS[p.view]||ALL_CHUNKS;
  return [];
}
if(document.readyState==='loading'){
  const plan=uniq(deepPlan()).filter(name=>!ready(name));
  if(plan.length){
    root.dataset.mingData='loading';root.dataset.mingDataReason='deep-link';
    plan.forEach(name=>document.write('<script src="assets/data-'+name+'.js" data-ming-data-chunk="'+name+'"><\/script>'));
  }
}

function loadChunk(name,reason){
  if(ready(name))return Promise.resolve(name);
  if(chunkPromises[name])return chunkPromises[name];
  chunkPromises[name]=new Promise((resolve,reject)=>{
    const script=document.createElement('script');
    script.src='assets/data-'+name+'.js';script.dataset.mingDataChunk=name;
    script.onload=()=>{
      if(!ready(name)){reject(new Error('data-'+name+'.js 已加载但未标记 ready'));return;}
      syncDataState(reason||('chunk:'+name));resolve(name);
    };
    script.onerror=()=>reject(new Error('领域数据加载失败：'+name));
    document.head.appendChild(script);
  }).catch(err=>{delete chunkPromises[name];syncDataState('error:'+name);throw err;});
  return chunkPromises[name];
}

window.__MING_ENSURE_DATA_CHUNKS=function(names,reason){
  const wanted=uniq(names);
  if(!wanted.length){syncDataState(reason);return Promise.resolve(DATA);}
  root.dataset.mingData='loading';root.dataset.mingDataReason=reason||'interaction';
  return Promise.all(wanted.map(name=>loadChunk(name,reason))).then(()=>{
    syncDataState(reason);return DATA;
  });
};
window.__MING_VIEW_CHUNKS=VIEW_CHUNKS;
window.__MING_ENTITY_PLAN=entityPlan;
window.__MING_ENSURE_VIEW_DATA=function(view,reason){return window.__MING_ENSURE_DATA_CHUNKS(VIEW_CHUNKS[view]||ALL_CHUNKS,reason||('view:'+view));};
window.__MING_ENSURE_ENTITY_DATA=function(kind,reason,id){
  const why=reason||('entity:'+kind);
  if(kind!=='event')return window.__MING_ENSURE_DATA_CHUNKS(entityPlan(kind,id),why);
  return window.__MING_ENSURE_DATA_CHUNKS(['events','insight'],why).then(()=>{
    const eventId=resolveEventId(id);
    if(!eventId)throw new Error('未找到事件：'+String(id||''));
    return window.__MING_ENSURE_DATA_CHUNKS(['locations','insight'],why);
  });
};

/* 命令面板搜索索引在当前 Classic UI 下不启用；此处直接解析为空，避免 404。 */
window.__MING_ENSURE_SEARCH_INDEX=function(){return Promise.resolve(null);};

window.__MING_ENSURE_FULL_DATA=function(reason){
  if(window.__MING_FULL_DATA_READY)return Promise.resolve(DATA);
  if(fullPromise)return fullPromise;
  fullPromise=window.__MING_ENSURE_DATA_CHUNKS(ALL_CHUNKS,reason||'full').then(data=>{
    syncDataState('full');return data;
  }).catch(err=>{fullPromise=null;throw err;});
  return fullPromise;
};

syncDataState();
})();
