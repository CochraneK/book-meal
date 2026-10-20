const fs = require("fs");
const html = fs.readFileSync("index.html", "utf8");
const marker = "const DATA=";
const start = html.indexOf(marker) + marker.length;
const end = html.indexOf("</script>", start);
let json = html.slice(start, end).trim();
if (json.endsWith(";")) json = json.slice(0, -1);
const DATA = JSON.parse(json);

function show(n) {
  const c = DATA.characters.find(x => x.name === n);
  if (!c) { console.log(n, "=> NOT FOUND"); return; }
  console.log("\n=== " + n + "  relations(" + c.relations.length + ") ===");
  c.relations.slice(0, 6).forEach(r =>
    console.log("  dir=" + r.dir, "other=" + r.other, "rel=" + r.rel, "ok=" + (!String(r.rel).includes("·"))));
}

["丁普郎", "俞通海", "傅友德", "朱元璋"].forEach(show);

const net = DATA.visualizations.relationNetwork.byName["朱元璋"];
if (net) {
  console.log("\n=== 朱元璋 ego neighbors(" + net.neighbors.length + ") ===");
  net.neighbors.slice(0, 8).forEach(nb =>
    console.log("  " + nb.name, "dir=" + nb.direction, "keyRel=" + nb.relation, "cat=" + nb.category));
}

// sanity: any relation rel still carrying 主动/反向 anywhere in ego data?
let bad = 0;
for (const name in DATA.visualizations.relationNetwork.byName) {
  for (const nb of DATA.visualizations.relationNetwork.byName[name].neighbors) {
    if (nb.relation && /(主动|反向)·/.test(nb.relation)) bad++;
  }
}
console.log("\nego edges with 主动/反向 prefix:", bad);
