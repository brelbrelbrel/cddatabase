# -*- coding: utf-8 -*-
import sqlite3, json

c = sqlite3.connect('music_database.db')
c.row_factory = sqlite3.Row
data = [dict(r) for r in c.execute('SELECT * FROM releases LIMIT 100')]

html = '''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Sort Test</title>
<style>body{background:#222;color:#fff;font-family:sans-serif;padding:20px}
.card{background:#333;padding:10px;margin:5px;border-radius:5px}
select{padding:10px;font-size:16px}</style></head>
<body>
<h1>Sort Test</h1>
<select id="sort" onchange="doSort()">
<option value="discogs">Discogs</option>
<option value="ebay">eBay</option>
<option value="yahoo">Yahoo</option>
</select>
<div id="status"></div>
<div id="grid"></div>
<script>
const data = DATA_PLACEHOLDER;
function doSort() {
  const s = document.getElementById('sort').value;
  document.getElementById('status').innerHTML = '<h2>Sort: ' + s + '</h2>';
  let sorted = [...data];
  if(s==='discogs') sorted.sort((a,b)=>(b.median_price||0)-(a.median_price||0));
  if(s==='ebay') sorted.sort((a,b)=>(b.ebay_sold_price||0)-(a.ebay_sold_price||0));
  if(s==='yahoo') sorted.sort((a,b)=>(b.yahoo_sold_price||0)-(a.yahoo_sold_price||0));
  document.getElementById('grid').innerHTML = sorted.slice(0,10).map(r =>
    '<div class="card"><b>'+(r.title||'?')+'</b><br>Discogs: $'+(r.median_price||0).toFixed(2)+' | eBay: $'+(r.ebay_sold_price||0).toFixed(2)+' | Yahoo: $'+(r.yahoo_sold_price||0).toFixed(2)+'</div>'
  ).join('');
}
doSort();
</script></body></html>'''

html = html.replace('DATA_PLACEHOLDER', json.dumps(data, ensure_ascii=False))
open('sort_test.html','w',encoding='utf-8').write(html)
print('Created sort_test.html')
