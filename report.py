"""Generate a comprehensive interactive HTML report from analyzed data."""

import json
import os
import re
from datetime import datetime
from config import OUTPUT_DIR


def _parse_date(raw):
    """Parse various date formats into 'DD Mon YYYY'."""
    if not raw:
        return ""
    try:
        dt = datetime.strptime(raw, "%a %b %d %H:%M:%S %z %Y")
        return dt.strftime("%d %b %Y")
    except (ValueError, TypeError):
        pass
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return dt.strftime("%d %b %Y")
    except (ValueError, TypeError):
        pass
    if re.search(r"\b20\d{2}\b", str(raw)):
        return raw
    return raw


REPORT_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Adara Ventures — Brand & Sentiment Report</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
/* ════════════════════════════════════════
   TOKENS
   ════════════════════════════════════════ */
:root {
  --c-bg:       #fafafa;
  --c-surface:  #ffffff;
  --c-border:   #e5e5e5;
  --c-text:     #1a1a1a;
  --c-text2:    #555;
  --c-text3:    #999;
  --c-accent:   #0047FF;
  --c-accent-bg:#eef2ff;
  --c-pos:      #00875a;
  --c-pos-bg:   #e6f4ee;
  --c-neu:      #777;
  --c-neu-bg:   #f0f0f0;
  --c-neg:      #de350b;
  --c-neg-bg:   #ffebe5;
  --c-black:    #0a0a0a;
  --radius:     10px;
  --shadow:     0 1px 3px rgba(0,0,0,.06);
  --nav-w:      220px;
  --transition: .35s cubic-bezier(.4,0,.2,1);
}
[data-theme="dark"] {
  --c-bg:       #111114;
  --c-surface:  #1a1a1f;
  --c-border:   #2a2a30;
  --c-text:     #e8e8ec;
  --c-text2:    #aaa;
  --c-text3:    #666;
  --c-accent:   #5b8aff;
  --c-accent-bg:#1a2240;
  --c-pos:      #36b37e;
  --c-pos-bg:   #1a2e24;
  --c-neu:      #888;
  --c-neu-bg:   #222228;
  --c-neg:      #ff5630;
  --c-neg-bg:   #2e1a1a;
  --c-black:    #fff;
  --shadow:     0 1px 4px rgba(0,0,0,.3);
}

/* ════════════════════════════════════════
   RESET & BASE
   ════════════════════════════════════════ */
*,*::before,*::after{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth;scroll-padding-top:32px}
body{
  font-family:'Inter',-apple-system,Helvetica Neue,sans-serif;
  background:var(--c-bg);color:var(--c-text);
  line-height:1.55;font-size:14px;
  -webkit-font-smoothing:antialiased;
  transition:background var(--transition),color var(--transition);
}

/* ════════════════════════════════════════
   LAYOUT
   ════════════════════════════════════════ */
.layout{display:flex;min-height:100vh}

/* ── Sidebar Nav ── */
.nav{
  position:sticky;top:0;height:100vh;
  width:var(--nav-w);min-width:var(--nav-w);
  padding:40px 24px;
  border-right:1px solid var(--c-border);
  background:var(--c-surface);
  display:flex;flex-direction:column;
  transition:background var(--transition),border var(--transition);
  z-index:100;
}
.nav-brand{
  font-size:11px;font-weight:700;letter-spacing:2.5px;
  text-transform:uppercase;color:var(--c-text3);margin-bottom:40px;
}
.nav-links{list-style:none;flex:1}
.nav-links li{margin-bottom:2px}
.nav-links a{
  display:flex;align-items:center;gap:10px;
  padding:8px 12px;border-radius:6px;
  font-size:12px;font-weight:500;color:var(--c-text2);
  text-decoration:none;transition:all .2s ease;
}
.nav-links a:hover{background:var(--c-bg);color:var(--c-text)}
.nav-links a.active{background:var(--c-accent-bg);color:var(--c-accent);font-weight:600}
.nav-links .num{
  font-size:10px;font-weight:600;letter-spacing:1px;
  color:var(--c-text3);min-width:20px;
  font-variant-numeric:tabular-nums;
}
.nav-bottom{margin-top:auto;padding-top:24px;border-top:1px solid var(--c-border)}
.theme-toggle{
  display:flex;align-items:center;gap:8px;
  padding:8px 12px;border-radius:6px;
  font-size:12px;font-weight:500;color:var(--c-text2);
  cursor:pointer;border:none;background:none;width:100%;
  transition:all .2s ease;
}
.theme-toggle:hover{background:var(--c-bg);color:var(--c-text)}
.theme-toggle svg{width:16px;height:16px;opacity:.6}

/* Mobile nav toggle */
.nav-toggle{
  display:none;position:fixed;top:16px;left:16px;z-index:200;
  width:40px;height:40px;border-radius:8px;
  background:var(--c-surface);border:1px solid var(--c-border);
  cursor:pointer;align-items:center;justify-content:center;
  box-shadow:var(--shadow);
}
.nav-toggle span{display:block;width:18px;height:2px;background:var(--c-text);
  position:relative;transition:all .2s}
.nav-toggle span::before,.nav-toggle span::after{
  content:'';position:absolute;width:18px;height:2px;background:var(--c-text);
  transition:all .2s}
.nav-toggle span::before{top:-6px}
.nav-toggle span::after{top:6px}

/* ── Main ── */
.main{flex:1;padding:56px 56px 96px;max-width:calc(100% - var(--nav-w));overflow-x:hidden}

/* ════════════════════════════════════════
   HEADER
   ════════════════════════════════════════ */
.header{margin-bottom:72px;padding-bottom:32px;border-bottom:3px solid var(--c-black)}
.header-eyebrow{
  font-size:11px;font-weight:600;letter-spacing:2.5px;
  text-transform:uppercase;color:var(--c-text3);margin-bottom:12px;
}
.header h1{
  font-size:52px;font-weight:800;letter-spacing:-2px;line-height:1.05;color:var(--c-black);
}
.header-meta{display:flex;gap:32px;margin-top:20px;font-size:13px;color:var(--c-text2);flex-wrap:wrap}
.header-meta span{font-weight:600;color:var(--c-text)}

/* ════════════════════════════════════════
   SECTIONS – scroll reveal
   ════════════════════════════════════════ */
.section{margin-bottom:80px;opacity:0;transform:translateY(24px);transition:opacity .6s ease,transform .6s ease}
.section.visible{opacity:1;transform:translateY(0)}
.section-num{
  font-size:10px;font-weight:700;letter-spacing:3px;
  text-transform:uppercase;color:var(--c-text3);margin-bottom:6px;
}
.section-title{
  font-size:22px;font-weight:700;letter-spacing:-.3px;color:var(--c-black);margin-bottom:32px;
}

/* ════════════════════════════════════════
   METRIC CARDS
   ════════════════════════════════════════ */
.metrics{
  display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:40px;
}
.metric{
  background:var(--c-surface);border:1px solid var(--c-border);
  border-radius:var(--radius);padding:24px;
  transition:transform .2s ease,box-shadow .2s ease,background var(--transition);
}
.metric:hover{transform:translateY(-2px);box-shadow:0 4px 16px rgba(0,0,0,.08)}
.metric-label{
  font-size:10px;font-weight:600;letter-spacing:2px;
  text-transform:uppercase;color:var(--c-text3);margin-bottom:8px;
}
.metric-value{font-size:36px;font-weight:800;letter-spacing:-1px;line-height:1;font-variant-numeric:tabular-nums}
.metric-value.pos{color:var(--c-pos)}
.metric-value.neg{color:var(--c-neg)}
.metric-value.neu{color:var(--c-neu)}

/* ════════════════════════════════════════
   SENTIMENT TRACK
   ════════════════════════════════════════ */
/* Gradient bloom sentiment bar */
.sentiment-bar-wrap{position:relative;margin:28px 0 20px}
.sentiment-bar-glow{
  position:absolute;inset:-6px -2px;border-radius:14px;
  background:linear-gradient(90deg,
    rgba(222,53,11,.25) 0%,
    rgba(222,53,11,.12) 20%,
    rgba(200,180,50,.08) 45%,
    rgba(0,135,90,.12) 80%,
    rgba(0,135,90,.25) 100%);
  filter:blur(10px);
  opacity:0;transition:opacity 1.2s ease;
}
.section.visible .sentiment-bar-glow{opacity:1}
.sentiment-bar-track{
  position:relative;height:12px;border-radius:6px;overflow:hidden;
  background:var(--c-border);
}
.sentiment-bar-fill{
  position:absolute;inset:0;border-radius:6px;
  background:linear-gradient(90deg,
    #d50000 0%,
    #ff5252 12%,
    #ffab91 25%,
    #ffe082 40%,
    #fff9c4 50%,
    #b9f6ca 65%,
    #69f0ae 80%,
    #00c853 100%);
  transform:scaleX(0);transform-origin:left;
  transition:transform 1.4s cubic-bezier(.22,1,.36,1);
}
.section.visible .sentiment-bar-fill{transform:scaleX(1)}
.sentiment-needle{
  position:absolute;top:-4px;width:3px;height:20px;
  background:var(--c-black);border-radius:2px;
  transform:translateX(-50%);
  box-shadow:0 0 0 3px var(--c-surface);
  transition:left 1.6s cubic-bezier(.22,1,.36,1),opacity .8s ease;
  opacity:0;z-index:2;
}
.section.visible .sentiment-needle{opacity:1}
.needle-label{
  position:absolute;top:-22px;left:50%;transform:translateX(-50%);
  font-size:10px;font-weight:700;letter-spacing:.5px;
  color:var(--c-text);white-space:nowrap;
  background:var(--c-surface);padding:1px 6px;border-radius:3px;
  border:1px solid var(--c-border);
}
.sentiment-scale{
  display:flex;justify-content:space-between;margin-top:10px;
  font-size:10px;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;color:var(--c-text3);
}
.sentiment-legend{display:flex;gap:24px;font-size:12px;color:var(--c-text2);margin-top:4px}
.dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px;vertical-align:middle}
.dot-pos{background:var(--c-pos)}.dot-neu{background:var(--c-border)}.dot-neg{background:var(--c-neg)}

/* ════════════════════════════════════════
   BRAND BARS
   ════════════════════════════════════════ */
.brand-grid{display:grid;gap:14px}
.brand-row{display:grid;grid-template-columns:140px 1fr 48px;align-items:center;gap:16px}
.brand-name{font-size:12px;font-weight:500;color:var(--c-text);text-transform:capitalize}
.brand-track{height:8px;background:var(--c-border);border-radius:4px;overflow:hidden}
.brand-fill{height:100%;border-radius:4px;background:var(--c-black);width:0;transition:width 1.2s cubic-bezier(.4,0,.2,1)}
.brand-count{font-size:12px;font-weight:700;color:var(--c-text2);text-align:right;font-variant-numeric:tabular-nums}

/* ════════════════════════════════════════
   SOURCE CARDS
   ════════════════════════════════════════ */
.source-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px}
.src-card{
  background:var(--c-surface);border:1px solid var(--c-border);
  border-radius:var(--radius);padding:24px;
  transition:transform .2s ease,box-shadow .2s ease,background var(--transition);
}
.src-card:hover{transform:translateY(-2px);box-shadow:0 4px 16px rgba(0,0,0,.08)}
.src-card h4{font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:1.5px;color:var(--c-text2);margin-bottom:12px}
.src-stat{font-size:32px;font-weight:800;letter-spacing:-.5px;color:var(--c-black)}
.src-detail{font-size:12px;color:var(--c-text2);margin-top:10px;line-height:1.8}
.src-detail strong{color:var(--c-text)}
.pill{
  display:inline-block;font-size:10px;font-weight:600;letter-spacing:.3px;
  padding:3px 8px;border-radius:4px;background:var(--c-bg);color:var(--c-text2);
  margin:2px 2px 2px 0;transition:background var(--transition);
}

/* ════════════════════════════════════════
   TABLES
   ════════════════════════════════════════ */
.table-wrap{
  background:var(--c-surface);border:1px solid var(--c-border);
  border-radius:var(--radius);overflow:hidden;
  transition:background var(--transition),border var(--transition);
}
table{width:100%;border-collapse:collapse;font-size:13px}
thead th{
  text-align:left;font-size:10px;font-weight:600;letter-spacing:1.5px;
  text-transform:uppercase;color:var(--c-text3);
  padding:14px 16px;border-bottom:1px solid var(--c-border);
  cursor:pointer;user-select:none;white-space:nowrap;
  transition:color .2s;position:relative;
}
thead th:hover{color:var(--c-text)}
thead th.r{text-align:right}
thead th .sort-icon{opacity:0;margin-left:4px;font-size:9px;transition:opacity .2s}
thead th:hover .sort-icon{opacity:.5}
thead th.sorted .sort-icon{opacity:1;color:var(--c-accent)}
tbody td{
  padding:14px 16px;border-bottom:1px solid var(--c-border);
  vertical-align:top;color:var(--c-text);transition:background .15s;
}
tbody td.r{text-align:right;font-variant-numeric:tabular-nums}
tbody tr:last-child td{border-bottom:none}
tbody tr{cursor:pointer;transition:background .15s}
tbody tr:hover{background:var(--c-bg)}
tbody tr.expanded{background:var(--c-accent-bg)}
.td-author{min-width:120px}
.td-author a{font-weight:600;color:var(--c-text);text-decoration:none;transition:color .2s}
.td-author a:hover{color:var(--c-accent)}
.td-author .sub{font-size:11px;color:var(--c-text3);margin-top:2px}
.td-text{max-width:420px;color:var(--c-text);line-height:1.55}
.td-text.expandable{position:relative}
.td-text .full{display:none;margin-top:8px;padding-top:8px;border-top:1px solid var(--c-border);font-size:12px;color:var(--c-text2);line-height:1.65}
tr.expanded .td-text .full{display:block}
.td-date{white-space:nowrap;color:var(--c-text3);font-variant-numeric:tabular-nums;font-size:12px}
.td-num{font-weight:600;font-variant-numeric:tabular-nums}
.td-sent{font-weight:700;font-variant-numeric:tabular-nums}
.td-sent.pos{color:var(--c-pos)}.td-sent.neg{color:var(--c-neg)}.td-sent.neu{color:var(--c-neu)}
.td-pill{font-size:11px;color:var(--c-text2)}
.tag-src{
  display:inline-block;font-size:10px;font-weight:600;letter-spacing:.5px;
  text-transform:uppercase;padding:3px 8px;border-radius:4px;
  background:var(--c-neu-bg);color:var(--c-neu);
  transition:background var(--transition),color var(--transition);
}
a{color:var(--c-accent);text-decoration:none}
a:hover{text-decoration:underline}

/* ════════════════════════════════════════
   FOOTER
   ════════════════════════════════════════ */
.footer{
  margin-top:96px;padding-top:24px;border-top:1px solid var(--c-border);
  font-size:11px;color:var(--c-text3);display:flex;justify-content:space-between;
  transition:border var(--transition);
}

/* ════════════════════════════════════════
   RESPONSIVE
   ════════════════════════════════════════ */
@media(max-width:1024px){
  .nav{position:fixed;left:0;top:0;transform:translateX(-100%);transition:transform .3s ease;box-shadow:none}
  .nav.open{transform:translateX(0);box-shadow:4px 0 24px rgba(0,0,0,.15)}
  .nav-toggle{display:flex}
  .main{max-width:100%;padding:56px 32px 96px}
  .metrics{grid-template-columns:repeat(3,1fr)}
}
@media(max-width:640px){
  .main{padding:72px 16px 64px}
  .header h1{font-size:32px;letter-spacing:-1px}
  .header-meta{flex-direction:column;gap:8px}
  .metrics{grid-template-columns:repeat(2,1fr)}
  .source-grid{grid-template-columns:1fr 1fr}
  .brand-row{grid-template-columns:100px 1fr 36px}
  .table-wrap{border-radius:0;border-left:none;border-right:none}
  .td-text{max-width:180px}
}

/* ════════════════════════════════════════
   OVERLAY for mobile nav
   ════════════════════════════════════════ */
.nav-overlay{
  display:none;position:fixed;inset:0;background:rgba(0,0,0,.3);z-index:99;
  opacity:0;transition:opacity .3s;
}
.nav-overlay.show{display:block;opacity:1}
</style>
</head>
<body>

<!-- Mobile nav toggle -->
<button class="nav-toggle" onclick="toggleNav()" aria-label="Menu"><span></span></button>
<div class="nav-overlay" onclick="toggleNav()"></div>

<div class="layout">

<!-- ═══ SIDEBAR ═══ -->
<nav class="nav" id="sidebar">
  <div class="nav-brand">Adara Ventures</div>
  <ul class="nav-links">
    <li><a href="#overview" class="active"><span class="num">01</span>Overview</a></li>
    <li><a href="#brand"><span class="num">02</span>Brand Signals</a></li>
    <li><a href="#sources"><span class="num">03</span>Sources</a></li>
    <li><a href="#linkedin"><span class="num">04</span>LinkedIn</a></li>
    <li><a href="#twitter"><span class="num">05</span>Twitter / X</a></li>
    <li><a href="#positive"><span class="num">06</span>Positive</a></li>
    <li><a href="#critical"><span class="num">07</span>Critical</a></li>
  </ul>
  <div class="nav-bottom">
    <button class="theme-toggle" onclick="toggleTheme()">
      <svg id="icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
      <svg id="icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="display:none"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
      <span id="theme-label">Dark mode</span>
    </button>
  </div>
</nav>

<!-- ═══ MAIN ═══ -->
<main class="main">

  <header class="header">
    <div class="header-eyebrow">Brand & Sentiment Intelligence</div>
    <h1>Adara Ventures</h1>
    <div class="header-meta">
      <div>Generated <span>$generated_date</span></div>
      <div>Data points <span>$total_items</span></div>
      <div>Sources <span>Google, News, LinkedIn, Twitter/X</span></div>
    </div>
  </header>

  <!-- ── 01 Overview ── -->
  <section class="section" id="overview">
    <div class="section-num">01</div>
    <h2 class="section-title">Overview</h2>
    <div class="metrics">
      <div class="metric"><div class="metric-label">Data Points</div><div class="metric-value" data-count="$total_items">0</div></div>
      <div class="metric"><div class="metric-label">Sentiment</div><div class="metric-value $polarity_class">$avg_polarity</div></div>
      <div class="metric"><div class="metric-label">Positive</div><div class="metric-value pos" data-count="$positive_count">0</div></div>
      <div class="metric"><div class="metric-label">Neutral</div><div class="metric-value neu" data-count="$neutral_count">0</div></div>
      <div class="metric"><div class="metric-label">Negative</div><div class="metric-value neg" data-count="$negative_count">0</div></div>
    </div>
    <div class="sentiment-bar-wrap">
      <div class="sentiment-bar-glow"></div>
      <div class="sentiment-bar-track">
        <div class="sentiment-bar-fill"></div>
        <div class="sentiment-needle" style="left:$needle_pct%">
          <div class="needle-label">$avg_polarity</div>
        </div>
      </div>
      <div class="sentiment-scale"><span>Negative</span><span>Neutral</span><span>Positive</span></div>
      <!-- needle_pct: 0%=left/negative, 100%=right/positive -->
    </div>
    <div class="sentiment-legend">
      <div><span class="dot dot-pos"></span>Positive $positive_pct%</div>
      <div><span class="dot dot-neu"></span>Neutral $neutral_pct%</div>
      <div><span class="dot dot-neg"></span>Negative $negative_pct%</div>
    </div>
  </section>

  <!-- ── 02 Brand ── -->
  <section class="section" id="brand">
    <div class="section-num">02</div>
    <h2 class="section-title">Brand Positioning Signals</h2>
    <div class="brand-grid">$brand_bars_html</div>
  </section>

  <!-- ── 03 Sources ── -->
  <section class="section" id="sources">
    <div class="section-num">03</div>
    <h2 class="section-title">Source Breakdown</h2>
    <div class="source-grid">$source_cards_html</div>
  </section>

  <!-- ── 04 LinkedIn ── -->
  <section class="section" id="linkedin">
    <div class="section-num">04</div>
    <h2 class="section-title">LinkedIn Engagement</h2>
    <div class="table-wrap">
    <table data-sortable>
      <thead><tr>
        <th>Author</th><th>Post</th>
        <th class="r" data-type="num">Likes <span class="sort-icon">&#9650;</span></th>
        <th class="r" data-type="num">Comments <span class="sort-icon">&#9650;</span></th>
        <th class="r" data-type="num">Shares <span class="sort-icon">&#9650;</span></th>
        <th>Date</th>
        <th class="r" data-type="num">Sent. <span class="sort-icon">&#9650;</span></th>
      </tr></thead>
      <tbody>$linkedin_rows_html</tbody>
    </table>
    </div>
  </section>

  <!-- ── 05 Twitter ── -->
  <section class="section" id="twitter">
    <div class="section-num">05</div>
    <h2 class="section-title">Twitter / X Engagement</h2>
    <div class="table-wrap">
    <table data-sortable>
      <thead><tr>
        <th>User</th><th>Tweet</th>
        <th class="r" data-type="num">Views <span class="sort-icon">&#9650;</span></th>
        <th class="r" data-type="num">Likes <span class="sort-icon">&#9650;</span></th>
        <th class="r" data-type="num">RTs <span class="sort-icon">&#9650;</span></th>
        <th class="r" data-type="num">Replies <span class="sort-icon">&#9650;</span></th>
        <th>Date</th>
        <th class="r" data-type="num">Sent. <span class="sort-icon">&#9650;</span></th>
      </tr></thead>
      <tbody>$twitter_rows_html</tbody>
    </table>
    </div>
  </section>

  <!-- ── 06 Positive ── -->
  <section class="section" id="positive">
    <div class="section-num">06</div>
    <h2 class="section-title">Most Positive Mentions</h2>
    <div class="table-wrap">
    <table data-sortable>
      <thead><tr>
        <th>Source</th><th>Title / Text</th>
        <th class="r" data-type="num">Polarity <span class="sort-icon">&#9650;</span></th>
        <th>Signals</th>
      </tr></thead>
      <tbody>$positive_rows_html</tbody>
    </table>
    </div>
  </section>

  <!-- ── 07 Critical ── -->
  <section class="section" id="critical">
    <div class="section-num">07</div>
    <h2 class="section-title">Critical Mentions</h2>
    <div class="table-wrap">
    <table data-sortable>
      <thead><tr>
        <th>Source</th><th>Title / Text</th>
        <th class="r" data-type="num">Polarity <span class="sort-icon">&#9650;</span></th>
        <th>Signals</th>
      </tr></thead>
      <tbody>$negative_rows_html</tbody>
    </table>
    </div>
  </section>

  <footer class="footer">
    <div>Adara Scraping Pipeline &middot; Apify + Domain-Aware Sentiment</div>
    <div>$generated_date</div>
  </footer>

</main>
</div>

<!-- ═══════════════════════════════════════
     JAVASCRIPT
     ═══════════════════════════════════════ -->
<script>
/* ── Dark mode ── */
function toggleTheme(){
  const html=document.documentElement;
  const isDark=html.getAttribute('data-theme')==='dark';
  html.setAttribute('data-theme',isDark?'light':'dark');
  document.getElementById('icon-sun').style.display=isDark?'block':'none';
  document.getElementById('icon-moon').style.display=isDark?'none':'block';
  document.getElementById('theme-label').textContent=isDark?'Dark mode':'Light mode';
  localStorage.setItem('theme',isDark?'light':'dark');
}
(function(){
  const saved=localStorage.getItem('theme');
  if(saved==='dark'){
    document.documentElement.setAttribute('data-theme','dark');
    document.getElementById('icon-sun').style.display='none';
    document.getElementById('icon-moon').style.display='block';
    document.getElementById('theme-label').textContent='Light mode';
  }
})();

/* ── Mobile nav ── */
function toggleNav(){
  document.getElementById('sidebar').classList.toggle('open');
  document.querySelector('.nav-overlay').classList.toggle('show');
}

/* ── Scroll reveal + active nav ── */
const sections=document.querySelectorAll('.section');
const navLinks=document.querySelectorAll('.nav-links a');
const revealObserver=new IntersectionObserver((entries)=>{
  entries.forEach(e=>{
    if(e.isIntersecting){
      e.target.classList.add('visible');
      // Activate nav link
      const id=e.target.id;
      navLinks.forEach(l=>{l.classList.toggle('active',l.getAttribute('href')==='#'+id)});
      // Trigger brand bar animation
      if(id==='brand'){
        e.target.querySelectorAll('.brand-fill').forEach(b=>{b.style.width=b.dataset.w});
      }
    }
  });
},{threshold:0.15,rootMargin:'0px 0px -10% 0px'});
sections.forEach(s=>revealObserver.observe(s));

/* ── Animated counters ── */
const counterObserver=new IntersectionObserver((entries)=>{
  entries.forEach(e=>{
    if(!e.isIntersecting)return;
    e.target.querySelectorAll('[data-count]').forEach(el=>{
      const target=parseInt(el.dataset.count);if(isNaN(target))return;
      const duration=800;const start=performance.now();
      function tick(now){
        const progress=Math.min((now-start)/duration,1);
        const eased=1-Math.pow(1-progress,3);
        el.textContent=Math.round(eased*target);
        if(progress<1)requestAnimationFrame(tick);
      }
      requestAnimationFrame(tick);
    });
    counterObserver.unobserve(e.target);
  });
},{threshold:0.3});
document.querySelectorAll('.metrics').forEach(m=>counterObserver.observe(m));

/* ── Sortable tables ── */
document.querySelectorAll('table[data-sortable] thead th[data-type]').forEach(th=>{
  th.addEventListener('click',()=>{
    const table=th.closest('table');
    const tbody=table.querySelector('tbody');
    const idx=[...th.parentNode.children].indexOf(th);
    const rows=[...tbody.querySelectorAll('tr')];
    const asc=th.classList.contains('sorted')&&th.dataset.dir==='asc';
    // Reset all
    table.querySelectorAll('th').forEach(h=>{h.classList.remove('sorted');h.dataset.dir=''});
    th.classList.add('sorted');
    th.dataset.dir=asc?'desc':'asc';
    th.querySelector('.sort-icon').innerHTML=asc?'&#9660;':'&#9650;';
    rows.sort((a,b)=>{
      let va=a.children[idx]?.textContent.replace(/[^0-9.\-+]/g,'')||'0';
      let vb=b.children[idx]?.textContent.replace(/[^0-9.\-+]/g,'')||'0';
      va=parseFloat(va);vb=parseFloat(vb);
      return asc?(va-vb):(vb-va);
    });
    rows.forEach(r=>tbody.appendChild(r));
  });
});

/* ── Expandable rows ── */
document.querySelectorAll('tbody tr').forEach(row=>{
  row.addEventListener('click',(e)=>{
    if(e.target.closest('a'))return;
    row.classList.toggle('expanded');
  });
});

/* ── Close mobile nav on link click ── */
navLinks.forEach(l=>l.addEventListener('click',()=>{
  document.getElementById('sidebar').classList.remove('open');
  document.querySelector('.nav-overlay').classList.remove('show');
}));
</script>
</body>
</html>"""


def generate_report():
    """Generate an HTML report from the analyzed data."""
    report_path = os.path.join(OUTPUT_DIR, "report_data.json")
    if not os.path.exists(report_path):
        print("  [Report] No report_data.json found. Run analysis first.")
        return

    with open(report_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    overall = data["overall"]
    dist = overall.get("sentiment_distribution", {})
    total = overall["total_items_analyzed"] or 1

    positive_count = dist.get("positive", 0)
    neutral_count = dist.get("neutral", 0)
    negative_count = dist.get("negative", 0)

    positive_pct = round((positive_count / total) * 100)
    neutral_pct = round((neutral_count / total) * 100)
    negative_pct = round((negative_count / total) * 100)

    polarity = overall["avg_polarity"]
    polarity_class = "pos" if polarity > 0.05 else ("neg" if polarity < -0.05 else "neu")

    # Sentiment segments
    bar_parts = []
    for cls, count in [("seg-pos", positive_count), ("seg-neu", neutral_count), ("seg-neg", negative_count)]:
        pct = (count / total) * 100 if total else 0
        if pct > 0:
            bar_parts.append(f'<div class="{cls}" style="width:{pct:.1f}%"></div>')
    sentiment_bar_html = "\n".join(bar_parts)

    # Brand bars – use data-w for animated fill
    brand_freq = overall.get("brand_signal_frequency", {})
    max_brand = max(brand_freq.values()) if brand_freq else 1
    brand_bars = []
    for cat, count in sorted(brand_freq.items(), key=lambda x: -x[1]):
        width = (count / max_brand) * 100
        label = cat.replace("_", " ")
        brand_bars.append(
            f'<div class="brand-row">'
            f'<div class="brand-name">{label}</div>'
            f'<div class="brand-track"><div class="brand-fill" data-w="{width:.0f}%"></div></div>'
            f'<div class="brand-count">{count}</div>'
            f'</div>'
        )
    brand_bars_html = "\n".join(brand_bars)

    # Source cards
    source_cards = []
    for src, info in data.get("by_source", {}).items():
        sd = info.get("sentiment_distribution", {})
        signals_html = " ".join(f'<span class="pill">{k.replace("_"," ")}</span>' for k in list(info.get("top_brand_signals", {}).keys())[:4])
        card = f"""<div class="src-card">
            <h4>{src.replace('_', ' ')}</h4>
            <div class="src-stat">{info['total_items']}</div>
            <div class="src-detail">
                Polarity <strong>{info['avg_polarity']:+.3f}</strong><br>
                <strong style="color:var(--c-pos)">{sd.get('positive',0)}</strong> pos &middot;
                <strong>{sd.get('neutral',0)}</strong> neu &middot;
                <strong style="color:var(--c-neg)">{sd.get('negative',0)}</strong> neg<br>
                {signals_html}
            </div>
        </div>"""
        source_cards.append(card)
    source_cards_html = "\n".join(source_cards)

    # Positive rows
    positive_rows = []
    for item in data.get("most_positive", []):
        title = item.get("title", item.get("text", ""))[:140]
        url = item.get("url", "")
        link = f'<a href="{url}">{title}</a>' if url else title
        signals = " ".join(f'<span class="pill">{s.replace("_"," ")}</span>' for s in item.get("brand_signals", {}).keys())
        pol = item.get("sentiment", {}).get("polarity", 0)
        positive_rows.append(
            f'<tr><td><span class="tag-src">{item.get("source","")}</span></td>'
            f'<td class="td-text">{link}</td>'
            f'<td class="r td-sent pos">{pol:+.2f}</td>'
            f'<td class="td-pill">{signals}</td></tr>'
        )
    positive_rows_html = "\n".join(positive_rows)

    # Negative rows
    negative_rows = []
    for item in data.get("most_negative", []):
        title = item.get("title", item.get("text", ""))[:140]
        url = item.get("url", "")
        link = f'<a href="{url}">{title}</a>' if url else title
        signals = " ".join(f'<span class="pill">{s.replace("_"," ")}</span>' for s in item.get("brand_signals", {}).keys())
        pol = item.get("sentiment", {}).get("polarity", 0)
        cls = "neg" if pol < -0.05 else "neu"
        negative_rows.append(
            f'<tr><td><span class="tag-src">{item.get("source","")}</span></td>'
            f'<td class="td-text">{link}</td>'
            f'<td class="r td-sent {cls}">{pol:+.2f}</td>'
            f'<td class="td-pill">{signals}</td></tr>'
        )
    negative_rows_html = "\n".join(negative_rows)

    # LinkedIn rows
    linkedin_rows = []
    for item in data.get("top_linkedin_engagement", []):
        text_full = item.get("text", "")
        text_short = text_full[:160] + ("..." if len(text_full) > 160 else "")
        text_rest = text_full[160:] if len(text_full) > 160 else ""
        author = item.get("author", "")
        author_followers = item.get("author_followers", "")
        url = item.get("url", "")
        likes = item.get("like_count", 0)
        comments = item.get("comment_count", 0)
        shares = item.get("share_count", 0)
        raw_date = item.get("date", "")
        date_str = _parse_date(raw_date) or item.get("time_since", "")
        pol = item.get("sentiment", {}).get("polarity", 0)
        cls = "pos" if pol > 0.05 else ("neg" if pol < -0.05 else "neu")
        author_cell = (
            f'<div class="td-author"><a href="{url}">{author}</a>'
            f'<div class="sub">{author_followers} followers</div></div>'
            if url else f'<div class="td-author">{author}</div>'
        )
        expand_html = f'<div class="full">{text_rest}</div>' if text_rest else ""
        linkedin_rows.append(
            f'<tr><td>{author_cell}</td>'
            f'<td class="td-text expandable">{text_short}{expand_html}</td>'
            f'<td class="r td-num">{likes}</td>'
            f'<td class="r td-num">{comments}</td>'
            f'<td class="r td-num">{shares}</td>'
            f'<td class="td-date">{date_str}</td>'
            f'<td class="r td-sent {cls}">{pol:+.2f}</td></tr>'
        )
    linkedin_rows_html = "\n".join(linkedin_rows) if linkedin_rows else '<tr><td colspan="7" style="color:var(--c-text3)">No data</td></tr>'

    # Twitter rows
    twitter_rows = []
    for item in data.get("top_twitter_engagement", []):
        text_full = item.get("text", "")
        text_short = text_full[:160] + ("..." if len(text_full) > 160 else "")
        text_rest = text_full[160:] if len(text_full) > 160 else ""
        user = item.get("user", "")
        user_name = item.get("user_name", "")
        url = item.get("url", "")
        views = item.get("view_count", 0)
        likes = item.get("like_count", 0)
        rts = item.get("retweet_count", 0)
        replies = item.get("reply_count", 0)
        raw_date = item.get("date", "")
        date_str = _parse_date(raw_date)
        pol = item.get("sentiment", {}).get("polarity", 0)
        cls = "pos" if pol > 0.05 else ("neg" if pol < -0.05 else "neu")
        user_link = f'<a href="{url}">@{user}</a>' if url else f"@{user}"
        user_cell = f'<div class="td-author">{user_link}<div class="sub">{user_name}</div></div>'
        expand_html = f'<div class="full">{text_rest}</div>' if text_rest else ""
        twitter_rows.append(
            f'<tr><td>{user_cell}</td>'
            f'<td class="td-text expandable">{text_short}{expand_html}</td>'
            f'<td class="r td-num">{views:,}</td>'
            f'<td class="r td-num">{likes}</td>'
            f'<td class="r td-num">{rts}</td>'
            f'<td class="r td-num">{replies}</td>'
            f'<td class="td-date">{date_str}</td>'
            f'<td class="r td-sent {cls}">{pol:+.2f}</td></tr>'
        )
    twitter_rows_html = "\n".join(twitter_rows) if twitter_rows else '<tr><td colspan="8" style="color:var(--c-text3)">No data</td></tr>'

    from string import Template
    tmpl = Template(REPORT_TEMPLATE)
    html = tmpl.safe_substitute(
        generated_date=datetime.now().strftime("%d %B %Y"),
        total_items=total,
        avg_polarity=f"{polarity:+.3f}",
        polarity_class=polarity_class,
        positive_count=positive_count,
        neutral_count=neutral_count,
        negative_count=negative_count,
        positive_pct=positive_pct,
        neutral_pct=neutral_pct,
        negative_pct=negative_pct,
        sentiment_bar_html=sentiment_bar_html,
        needle_pct=round((polarity + 1) / 2 * 100),  # map -1..+1 to 0..100%
        brand_bars_html=brand_bars_html,
        source_cards_html=source_cards_html,
        positive_rows_html=positive_rows_html,
        negative_rows_html=negative_rows_html,
        linkedin_rows_html=linkedin_rows_html,
        twitter_rows_html=twitter_rows_html,
    )

    html_path = os.path.join(OUTPUT_DIR, "adara_ventures_report.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"  [Report] HTML report saved to: {html_path}")
    return html_path


if __name__ == "__main__":
    generate_report()
