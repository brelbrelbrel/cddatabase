# -*- coding: utf-8 -*-
import sqlite3
import json

DB_PATH = r"C:\Users\kawamura\Desktop\music_database.db"
c = sqlite3.connect(DB_PATH)
c.row_factory = sqlite3.Row
releases = c.execute('''SELECT * FROM releases ORDER BY
    CASE WHEN median_price IS NOT NULL AND median_price > 0 THEN 0 ELSE 1 END,
    median_price DESC, community_want DESC''').fetchall()
cols = [k for k in releases[0].keys()] if releases else []
data = [dict(r) for r in releases]

html = '''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>Music Database - 中央値ランキング</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,sans-serif;background:#1a1a2e;color:#eee;padding:20px}
h1{text-align:center;color:#00d4ff;margin-bottom:20px}
.controls{display:flex;gap:10px;margin-bottom:20px;flex-wrap:wrap;justify-content:center}
input,select{padding:10px;border:none;border-radius:5px;background:#16213e;color:#eee;font-size:14px}
input{width:250px}
.stats{text-align:center;margin-bottom:20px;color:#888}
.filter-btn{padding:8px 15px;border:none;border-radius:5px;cursor:pointer;font-size:13px}
.filter-btn.active{background:#ffd93d;color:#000}
.filter-btn:not(.active){background:#16213e;color:#888}
.ranking{margin-bottom:30px}
.ranking h2{color:#ffd93d;text-align:center;margin-bottom:15px}
.ranking-list{display:flex;gap:15px;overflow-x:auto;padding:10px 0}
.ranking-item{min-width:120px;text-align:center;cursor:pointer}
.ranking-item:hover{transform:scale(1.05)}
.ranking-item img{width:100px;height:100px;object-fit:cover;border-radius:5px}
.ranking-num{font-size:20px;font-weight:bold;color:#ffd93d}
.ranking-price{color:#00ff88;font-weight:bold}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:20px}
.card{background:#16213e;border-radius:10px;overflow:hidden;cursor:pointer;transition:transform 0.2s}
.card:hover{transform:translateY(-5px);box-shadow:0 10px 30px rgba(0,212,255,0.2)}
.card img{width:100%;height:180px;object-fit:cover;background:#0f3460}
.card-body{padding:15px}
.card-title{font-size:13px;font-weight:bold;margin-bottom:5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.card-catalog{color:#ffd93d;font-family:monospace;font-size:12px}
.card-info{font-size:11px;color:#888;margin:3px 0}
.card-price{color:#00ff88;font-weight:bold}
.card-median{color:#00d4ff;font-weight:bold}
.card-want{color:#ff6b6b}
.no-data-badge{background:#ff6b6b;color:#fff;font-size:10px;padding:2px 6px;border-radius:3px}
.modal{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.9);z-index:1000;overflow-y:auto}
.modal-content{max-width:700px;margin:30px auto;background:#16213e;border-radius:10px;padding:25px}
.modal-close{float:right;font-size:28px;cursor:pointer;color:#888}
.modal-close:hover{color:#fff}
.modal-img{width:100%;max-height:350px;object-fit:contain;margin-bottom:15px;border-radius:5px}
.modal h2{margin-bottom:15px}
.modal p{margin:8px 0}
.genre-tag{display:inline-block;background:#0f3460;padding:3px 8px;border-radius:3px;margin:2px;font-size:11px}
.tracklist{background:#0f3460;padding:15px;border-radius:5px;margin-top:15px;max-height:200px;overflow-y:auto}
.tracklist li{margin:5px 0;font-size:13px}
.play-btn{background:#00d4ff;color:#000;padding:10px 20px;border:none;border-radius:5px;cursor:pointer;font-weight:bold;margin-top:15px}
.play-btn:hover{background:#00a8cc}
audio{width:100%;margin-top:15px}
.no-img{background:#0f3460;display:flex;align-items:center;justify-content:center;color:#444;font-size:40px;height:180px}
.price-box{background:#0f3460;padding:15px;border-radius:8px;margin:15px 0}
.price-row{display:flex;justify-content:space-between;margin:5px 0}
.price-label{color:#888}
.price-value{font-weight:bold}
.price-median{color:#00d4ff;font-size:24px}
.price-high{color:#ffd93d}
.price-low{color:#888}
.last-sold{color:#aaa;font-size:12px;margin-top:10px}
</style>
</head>
<body>
<h1>Music Database - 販売価格ランキング</h1>
<div class="controls">
<input type="text" id="search" placeholder="Search..." oninput="doFilter()">
<select id="genre" onchange="doFilter()"><option value="">All Genres</option></select>
<select id="sort" onchange="doFilter()">
<option value="median_desc">Discogs 高い順</option>
<option value="ebay_desc">eBay 高い順</option>
<option value="yahoo_desc">ヤフオク 高い順</option>
<option value="mercari_desc">メルカリ 高い順</option>
<option value="median_asc">Discogs 低い順</option>
<option value="ebay_asc">eBay 低い順</option>
<option value="yahoo_asc">ヤフオク 低い順</option>
<option value="mercari_asc">メルカリ 低い順</option>
<option value="want_desc">Want数</option>
<option value="year_desc">年代</option>
<option value="name">名前順</option>
</select>
<button class="filter-btn active" id="filterAll" onclick="setFilter('all')">全て</button>
<button class="filter-btn" id="filterWithPrice" onclick="setFilter('withPrice')">価格あり</button>
<button class="filter-btn" id="filterNoPrice" onclick="setFilter('noPrice')">価格なし</button>
</div>
<div class="stats" id="stats"></div>
<div class="ranking"><h2>中央値 TOP 10 (USD)</h2><div class="ranking-list" id="ranking"></div></div>
<div class="grid" id="grid"></div>
<div class="modal" id="modal" onclick="if(event.target===this)closeModal()">
<div class="modal-content" id="modalContent"></div>
</div>
<script>
const data=DATA_PLACEHOLDER;
let filtered=[...data];
let priceFilter='all';

document.getElementById("search").addEventListener("input", doFilter);
document.getElementById("genre").addEventListener("change", doFilter);
document.getElementById("sort").addEventListener("change", doFilter);

function init(){
  const genres=[...new Set(data.map(r=>r.genre_folder).filter(g=>g))].sort();
  const sel=document.getElementById("genre");
  genres.forEach(g=>{const o=document.createElement("option");o.value=g;o.textContent=g;sel.appendChild(o)});
  showRanking();
  doFilter();
}

function getImg(r){
  if(r.local_image) return "file:///"+r.local_image.replace(/\\\\/g,"/");
  return r.thumb_url||"";
}

function setFilter(f){
  priceFilter=f;
  document.querySelectorAll('.filter-btn').forEach(b=>b.classList.remove('active'));
  document.getElementById('filter'+f.charAt(0).toUpperCase()+f.slice(1)).classList.add('active');
  doFilter();
}

function showRanking(){
  // Group by discogs_id to avoid duplicates
  const seen=new Set();
  const ranked=data.filter(r=>{
    if(!r.median_price||r.median_price<=0)return false;
    if(seen.has(r.discogs_id))return false;
    seen.add(r.discogs_id);
    return true;
  }).sort((a,b)=>b.median_price-a.median_price).slice(0,10);

  document.getElementById("ranking").innerHTML=ranked.map((r,i)=>{
    const idx=data.indexOf(r);
    return `<div class="ranking-item" onclick="showDetail(${idx})">
      <div class="ranking-num">#${i+1}</div>
      <img src="${getImg(r)}" onerror="this.outerHTML='<div class=no-img>?</div>'">
      <div class="ranking-price">$${r.median_price.toFixed(2)}</div>
      <div style="font-size:10px;color:#888">${(r.title||'').substring(0,20)}</div>
    </div>`;
  }).join("");
}

function doFilter(){
  const q=document.getElementById("search").value.toLowerCase().trim();
  const g=document.getElementById("genre").value;
  const s=document.getElementById("sort").value;
  console.log("doFilter called, sort=", s);

  filtered=data.filter(r=>{
    const txt=((r.title||"")+(r.catalog_number||"")+(r.label||"")+(r.filename||"")+(r.genre||"")).toLowerCase();
    const matchQ = !q || txt.includes(q);
    const matchG = !g || r.genre_folder===g;
    let matchP = true;
    if(priceFilter==='withPrice') matchP = r.median_price && r.median_price > 0;
    if(priceFilter==='noPrice') matchP = !r.median_price || r.median_price <= 0;
    return matchQ && matchG && matchP;
  });

  filtered.sort((a,b)=>{
    switch(s){
      case "median_desc": return (b.median_price||0)-(a.median_price||0);
      case "median_asc": return (a.median_price||9999999)-(b.median_price||9999999);
      case "ebay_desc": return (b.ebay_sold_price||0)-(a.ebay_sold_price||0);
      case "ebay_asc": return (a.ebay_sold_price||9999999)-(b.ebay_sold_price||9999999);
      case "yahoo_desc": return (b.yahoo_sold_price||0)-(a.yahoo_sold_price||0);
      case "yahoo_asc": return (a.yahoo_sold_price||9999999)-(b.yahoo_sold_price||9999999);
      case "mercari_desc": return (b.mercari_sold_price||0)-(a.mercari_sold_price||0);
      case "mercari_asc": return (a.mercari_sold_price||9999999)-(b.mercari_sold_price||9999999);
      case "want_desc": return (b.community_want||0)-(a.community_want||0);
      case "year_desc": return (parseInt(b.year)||0)-(parseInt(a.year)||0);
      case "name": return (a.title||a.filename||"").localeCompare(b.title||b.filename||"");
    }
    return 0;
  });

  render();
}

function render(){
  document.getElementById("grid").innerHTML=filtered.map(r=>{
    const idx=data.indexOf(r);
    const hasPrice = r.median_price && r.median_price > 0;
    return `<div class="card" onclick="showDetail(${idx})">
      <img src="${getImg(r)}" onerror="this.outerHTML='<div class=no-img>?</div>'">
      <div class="card-body">
        <div class="card-title">${r.title||r.filename}</div>
        <div class="card-catalog">[${r.catalog_number||'N/A'}]</div>
        <div class="card-info">${r.label||''} ${r.year?'('+r.year+')':''}</div>
        ${hasPrice?`<div class="card-median">Discogs $${r.median_price.toFixed(2)}</div>`:''}
        ${r.ebay_sold_price?`<div class="card-price">eBay $${r.ebay_sold_price.toFixed(2)}</div>`:''}
        ${r.yahoo_sold_price?`<div class="card-info" style="color:#ff6b6b">ヤフオク $${r.yahoo_sold_price.toFixed(2)}</div>`:''}
        ${r.mercari_sold_price?`<div class="card-info" style="color:#ff9500">メルカリ $${r.mercari_sold_price.toFixed(2)}</div>`:''}
        ${!hasPrice && !r.ebay_sold_price && !r.yahoo_sold_price && !r.mercari_sold_price?'<span class="no-data-badge">価格なし</span>':''}
        ${r.community_want?`<div class="card-info card-want">${r.community_want} want</div>`:''}
      </div>
    </div>`;
  }).join("");

  const withPrice=data.filter(r=>r.median_price&&r.median_price>0).length;
  const noPrice=data.length-withPrice;
  const sortLabel=document.getElementById("sort").options[document.getElementById("sort").selectedIndex].text;
  document.getElementById("stats").innerHTML=`${filtered.length} / ${data.length} releases | <span style="color:#ffd93d">${sortLabel}</span> | <span style="color:#00ff88">${withPrice}件価格あり</span> | <span style="color:#ff6b6b">${noPrice}件価格なし</span>`;
}

function showDetail(i){
  const r=data[i];
  let tracks=[];try{tracks=JSON.parse(r.tracklist||"[]")}catch(e){}
  const fp=r.file_path.replace(/\\\\/g,"/");
  const hasPrice = r.median_price && r.median_price > 0;

  document.getElementById("modalContent").innerHTML=`
    <span class="modal-close" onclick="closeModal()">×</span>
    <img class="modal-img" src="${r.cover_url||getImg(r)}" onerror="this.style.display='none'">
    <h2>${r.title||r.filename}</h2>
    <p><strong>Catalog:</strong> <span class="card-catalog">${r.catalog_number||'N/A'}</span></p>
    <p><strong>Label:</strong> ${r.label||'?'}</p>
    <p><strong>Year:</strong> ${r.year||'?'} | <strong>Country:</strong> ${r.country||'?'}</p>
    <p><strong>Format:</strong> ${r.format||'?'}</p>
    ${r.genre?`<p><strong>Genre:</strong> ${r.genre.split(',').map(g=>`<span class="genre-tag">${g.trim()}</span>`).join('')}</p>`:''}

    <div class="price-box">
      <div style="display:flex;gap:15px;flex-wrap:wrap">
        <div style="flex:1;min-width:100px">
          <div style="color:#00d4ff;font-size:12px;margin-bottom:5px;font-weight:bold">Discogs</div>
          ${hasPrice?`<div style="color:#00d4ff;font-size:20px;font-weight:bold">$${r.median_price.toFixed(2)}</div>
          <div style="color:#888;font-size:11px">中央値</div>
          ${r.high_price?`<div style="color:#ffd93d;font-size:12px">$${r.high_price.toFixed(2)} 最高</div>`:''}`:'<div style="color:#666">-</div>'}
        </div>
        <div style="flex:1;min-width:100px">
          <div style="color:#00ff88;font-size:12px;margin-bottom:5px;font-weight:bold">eBay</div>
          ${r.ebay_sold_price?`<div style="color:#00ff88;font-size:20px;font-weight:bold">$${r.ebay_sold_price.toFixed(2)}</div>
          <div style="color:#888;font-size:11px">${r.ebay_sold_count||0}件販売</div>
          ${r.ebay_avg_price?`<div style="color:#aaa;font-size:12px">平均 $${r.ebay_avg_price.toFixed(2)}</div>`:''}`:'<div style="color:#666">-</div>'}
        </div>
        <div style="flex:1;min-width:100px">
          <div style="color:#ff6b6b;font-size:12px;margin-bottom:5px;font-weight:bold">ヤフオク</div>
          ${r.yahoo_sold_price?`<div style="color:#ff6b6b;font-size:20px;font-weight:bold">$${r.yahoo_sold_price.toFixed(2)}</div>
          <div style="color:#888;font-size:11px">${r.yahoo_sold_count||0}件落札</div>
          ${r.yahoo_avg_price?`<div style="color:#aaa;font-size:12px">平均 $${r.yahoo_avg_price.toFixed(2)}</div>`:''}`:'<div style="color:#666">-</div>'}
        </div>
        <div style="flex:1;min-width:100px">
          <div style="color:#ff9500;font-size:12px;margin-bottom:5px;font-weight:bold">メルカリ</div>
          ${r.mercari_sold_price?`<div style="color:#ff9500;font-size:20px;font-weight:bold">$${r.mercari_sold_price.toFixed(2)}</div>
          <div style="color:#888;font-size:11px">${r.mercari_sold_count||0}件販売</div>
          ${r.mercari_avg_price?`<div style="color:#aaa;font-size:12px">平均 $${r.mercari_avg_price.toFixed(2)}</div>`:''}`:'<div style="color:#666">-</div>'}
        </div>
      </div>
      ${r.lowest_price?`<div style="margin-top:10px;padding-top:10px;border-top:1px solid #333">
        <span class="price-label">Discogs出品最安:</span>
        <span style="color:#888">$${r.lowest_price.toFixed(2)} (${r.num_for_sale}件出品中)</span>
      </div>`:''}
      ${r.last_sold_date?`<div class="last-sold">Discogs最終取引: ${r.last_sold_date.substring(0,10)}</div>`:''}
    </div>

    ${r.community_want?`<p class="card-want">${r.community_want} want / ${r.community_have} have</p>`:''}
    ${r.discogs_url?`<p><a href="${r.discogs_url}" target="_blank" style="color:#00d4ff">View on Discogs →</a></p>`:''}
    <p style="font-size:11px;color:#666">File: ${r.file_path}</p>
    <button class="play-btn" onclick="play('${fp}')">▶ Play</button>
    <audio id="audio" controls style="display:none"></audio>
    ${tracks.length?`<div class="tracklist"><strong>Tracklist:</strong><ol>${tracks.map(t=>`<li>${t}</li>`).join('')}</ol></div>`:''}
  `;
  document.getElementById("modal").style.display="block";
}

function closeModal(){document.getElementById("modal").style.display="none";const a=document.getElementById("audio");if(a)a.pause()}
function play(p){const a=document.getElementById("audio");a.src="file:///"+p;a.style.display="block";a.play()}
document.onkeydown=e=>{if(e.key==="Escape")closeModal()};
init();
</script>
</body>
</html>'''

html = html.replace('DATA_PLACEHOLDER', json.dumps(data, ensure_ascii=False))

HTML_PATH = r"C:\Users\kawamura\Desktop\music_database.html"
with open(HTML_PATH, 'w', encoding='utf-8') as f:
    f.write(html)

print('HTML updated! Total:', len(data), 'releases')
print('※直近販売履歴をスクレイピング予定')
import webbrowser
import os
webbrowser.open('file:///' + os.path.abspath('music_database.html').replace('\\', '/'))
