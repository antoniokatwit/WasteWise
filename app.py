"""
WasteWise — single file Flask app
===================================
Setup (run once in your VS Code terminal):
    pip install flask

Run:
    python app.py

Then open http://localhost:5000 in your browser.
On your phone (same Wi-Fi): http://YOUR_IP:5000
  Windows  -> ipconfig
  Mac/Linux -> ifconfig

No folders needed. HTML, CSS, database, and routes are all here.
"""

import os
import sqlite3
import uuid
from flask import Flask, g, jsonify, render_template_string, request, session

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "wastewise-dev-key")
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wastewise.db")

# ======================================================================
# DATABASE SCHEMA + SEED  (matches the cleaned schema exactly)
# ======================================================================

SCHEMA = """
DROP TABLE IF EXISTS sort_attempts;
DROP TABLE IF EXISTS components;
DROP TABLE IF EXISTS items;

CREATE TABLE items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    description TEXT NOT NULL,
    disassemble INTEGER NOT NULL DEFAULT 1,
    btn_label   TEXT NOT NULL DEFAULT 'Take it apart'
);

CREATE TABLE components (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id     INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    slug        TEXT NOT NULL,
    name        TEXT NOT NULL,
    correct_bin TEXT NOT NULL CHECK(correct_bin IN ('recycle','trash','compost'))
);

CREATE TABLE sort_attempts (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id   TEXT NOT NULL,
    component_id INTEGER NOT NULL REFERENCES components(id),
    chosen_bin   TEXT NOT NULL CHECK(chosen_bin IN ('recycle','trash','compost')),
    is_correct   INTEGER NOT NULL,
    attempted_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_attempts_session ON sort_attempts(session_id);
"""

SEED = """
INSERT INTO items (name, description, disassemble, btn_label) VALUES
('Starbucks Plastic Cup',    'A cold-drink Starbucks cup — clear plastic body, plastic lid, and a green plastic straw.', 1, 'Take it apart'),
('Plastic Soda Bottle',      'An empty plastic soda bottle with the cap still on.', 1, 'Prep it'),
('Yogurt Cup',               'A plastic yogurt cup with a peelable foil lid and leftover yogurt inside.', 1, 'Peel the lid & scrape'),
('Banana with Sticker',      'A banana peel with a tiny PLU produce sticker stuck on it.', 1, 'Peel off the sticker'),
('Orange Peels with Sticker','Orange peels with a produce sticker still on the skin.', 1, 'Peel off the sticker'),
('Chip Bag',                 'An empty potato chip bag — shiny, crinkly, and multilayer.', 0, ''),
('Paper',                    'A clean, dry sheet of office paper — no food stains or grease.', 0, ''),
('Paper Towel',              'A used paper towel from wiping up a spill.', 0, ''),
('Plastic Bag',              'A thin single-use plastic shopping bag.', 0, ''),
('Ziploc Bag',               'A Ziploc bag with leftover food crumbs inside.', 1, 'Empty the crumbs'),
('Glass Bottle',             'An empty glass beverage bottle — rinsed clean.', 0, ''),
('Aluminum Can',             'An empty aluminum soda or food can.', 0, ''),
('Candy Wrapper',            'A shiny candy or chocolate bar wrapper.', 0, ''),
('Bones',                    'Leftover chicken or beef bones from a meal.', 0, '');

INSERT INTO components (item_id, slug, name, correct_bin) VALUES
(1,  'straw',   'Plastic straw',         'trash'),
(1,  'lid',     'Plastic lid',           'trash'),
(1,  'cup',     'Clear plastic cup',     'recycle'),
(2,  'bottle',  'Rinsed plastic bottle', 'recycle'),
(2,  'liquid',  'Any remaining liquid',  'compost'),
(3,  'yogurt',  'Leftover yogurt',       'compost'),
(3,  'foil',    'Foil lid (rinsed)',     'recycle'),
(3,  'cup',     'Rinsed plastic cup',    'recycle'),
(4,  'sticker', 'Produce sticker',       'trash'),
(4,  'peel',    'Banana peel',           'compost'),
(5,  'sticker', 'Produce sticker',       'trash'),
(5,  'peels',   'Orange peels',          'compost'),
(6,  'bag',     'Chip bag',              'trash'),
(7,  'paper',   'Clean sheet of paper',  'recycle'),
(8,  'towel',   'Used paper towel',      'trash'),
(9,  'bag',     'Plastic shopping bag',  'trash'),
(10, 'crumbs',  'Food crumbs inside',    'compost'),
(10, 'bag',     'Empty Ziploc bag',      'trash'),
(11, 'bottle',  'Glass bottle',          'recycle'),
(12, 'can',     'Aluminum can',          'recycle'),
(13, 'wrapper', 'Candy wrapper',         'trash'),
(14, 'bones',   'Bones',                 'trash');
"""

# ======================================================================
# HTML + CSS  (no emojis anywhere)
# ======================================================================

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="theme-color" content="#1a3d2b">
<title>WasteWise</title>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,800;1,9..144,400&family=DM+Sans:wght@400;500;700&display=swap" rel="stylesheet">
<style>
:root {
  --green:       #1a3d2b;
  --green-mid:   #2d6a4f;
  --green-light: #52b788;
  --green-pale:  #d8f3dc;
  --amber:       #e9a820;
  --amber-pale:  #fef3d0;
  --blue:        #1a6fa0;
  --blue-pale:   #dbeeff;
  --cream:       #f7f3ec;
  --white:       #ffffff;
  --gray:        #6b7280;
  --border:      #e2ddd6;
  --shadow:      0 4px 24px rgba(0,0,0,.10);
  --fd: 'Fraunces', Georgia, serif;
  --fb: 'DM Sans', system-ui, sans-serif;
}

*, *::before, *::after {
  margin: 0; padding: 0; box-sizing: border-box;
  -webkit-tap-highlight-color: transparent;
}

body {
  font-family: var(--fb);
  background: var(--cream);
  color: var(--green);
  min-height: 100dvh;
  overflow-x: hidden;
  user-select: none;
  -webkit-font-smoothing: antialiased;
}

.screen { display: none; flex-direction: column; min-height: 100dvh; }
.screen.active { display: flex; }
.hidden { display: none !important; }

/* ── START SCREEN ── */
#screen-start {
  background: linear-gradient(170deg, var(--green) 0%, var(--green-mid) 100%);
  align-items: center;
  justify-content: center;
  padding: 48px 32px;
  text-align: center;
  gap: 0;
}

.logo {
  font-family: var(--fd);
  font-size: 56px;
  font-weight: 800;
  color: #fff;
  letter-spacing: -1px;
  line-height: 1;
  margin-bottom: 10px;
}
.logo span { color: var(--amber); font-style: italic; }

.tagline {
  font-size: 16px;
  color: rgba(255,255,255,.65);
  margin-bottom: 48px;
}

.bin-legend {
  display: flex;
  gap: 14px;
  justify-content: center;
  margin-bottom: 48px;
  flex-wrap: wrap;
}

.bin-pill {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  border-radius: 100px;
  font-size: 14px;
  font-weight: 700;
  letter-spacing: .04em;
}
.bin-pill .dot {
  width: 10px; height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}
.bin-pill.recycle { background: rgba(255,255,255,.12); color: #93c5fd; }
.bin-pill.recycle .dot { background: #93c5fd; }
.bin-pill.trash   { background: rgba(255,255,255,.12); color: rgba(255,255,255,.7); }
.bin-pill.trash   .dot { background: rgba(255,255,255,.6); }
.bin-pill.compost { background: rgba(255,255,255,.12); color: var(--green-pale); }
.bin-pill.compost .dot { background: var(--green-pale); }

.start-btn {
  background: var(--amber);
  color: var(--green);
  border: none;
  padding: 20px 52px;
  border-radius: 100px;
  font-family: var(--fb);
  font-size: 20px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 8px 32px rgba(233,168,32,.45);
  margin-bottom: 20px;
  transition: transform .15s;
}
.start-btn:active { transform: scale(.96); }

.start-note {
  font-size: 13px;
  color: rgba(255,255,255,.4);
}

/* ── TOPBAR ── */
.topbar {
  background: var(--green);
  padding: 14px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}
.topbar-logo {
  font-family: var(--fd);
  font-size: 20px;
  font-weight: 800;
  color: #fff;
}
.topbar-logo span { color: var(--amber); font-style: italic; }
.topbar-right { display: flex; align-items: center; gap: 10px; }
.topbar-prog  { font-size: 13px; color: rgba(255,255,255,.6); font-weight: 500; }
.topbar-score {
  background: rgba(255,255,255,.13);
  color: #fff;
  font-size: 14px;
  font-weight: 700;
  padding: 6px 14px;
  border-radius: 100px;
}
.topbar-score span { color: var(--amber); }

.prog-wrap { background: rgba(0,0,0,.2); height: 4px; flex-shrink: 0; }
.prog-fill  { height: 4px; background: var(--amber); transition: width .5s ease; }

/* ── GAME BODY ── */
.game-body {
  flex: 1;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  padding: 20px 16px 16px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

/* item card */
.item-card {
  background: var(--white);
  border-radius: 24px;
  padding: 28px 24px;
  box-shadow: var(--shadow);
  flex-shrink: 0;
}

.item-tag {
  display: inline-block;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: .1em;
  text-transform: uppercase;
  color: var(--green-mid);
  background: var(--green-pale);
  padding: 4px 12px;
  border-radius: 100px;
  margin-bottom: 12px;
}

.item-name {
  font-family: var(--fd);
  font-size: 26px;
  font-weight: 800;
  color: var(--green);
  line-height: 1.1;
  margin-bottom: 8px;
}

.item-desc {
  font-size: 14px;
  color: var(--gray);
  line-height: 1.6;
  margin-bottom: 20px;
}

.disassemble-btn {
  background: var(--amber);
  color: var(--green);
  border: none;
  padding: 14px 28px;
  border-radius: 100px;
  font-family: var(--fb);
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  transition: transform .15s;
  box-shadow: 0 4px 14px rgba(233,168,32,.30);
}
.disassemble-btn:active { transform: scale(.96); }

/* components zone */
.components-zone { flex-shrink: 0; }

.zone-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: .1em;
  text-transform: uppercase;
  color: var(--gray);
  margin-bottom: 10px;
}

.component-chip {
  background: var(--white);
  border: 2px solid var(--border);
  border-radius: 16px;
  padding: 14px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  cursor: pointer;
  transition: border-color .18s, background .18s, box-shadow .18s;
  margin-bottom: 10px;
}
.component-chip:last-child { margin-bottom: 0; }

.component-chip.selected {
  border-color: var(--amber);
  background: var(--amber-pale);
  box-shadow: 0 0 0 3px rgba(233,168,32,.20);
}
.component-chip.sorted-recycle { border-color: var(--blue);         background: var(--blue-pale);  cursor: default; }
.component-chip.sorted-trash   { border-color: #9ca3af;             background: #f5f5f5;           cursor: default; }
.component-chip.sorted-compost { border-color: var(--green-light);  background: var(--green-pale); cursor: default; }

@keyframes wrongFlash {
  0%,100% { background: var(--white); border-color: var(--border); }
  35%      { background: #fde8e8;     border-color: #e05555; }
}
.component-chip.wrong-flash { animation: wrongFlash .5s ease; }

.chip-left { display: flex; flex-direction: column; gap: 2px; }

.chip-name {
  font-size: 15px;
  font-weight: 700;
  color: var(--green);
}

.chip-status {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: .05em;
  text-transform: uppercase;
  padding: 3px 10px;
  border-radius: 100px;
  opacity: 0;
  transition: opacity .2s;
  white-space: nowrap;
  flex-shrink: 0;
  align-self: center;
}
.component-chip.sorted-recycle .chip-status { opacity: 1; background: var(--blue);      color: #fff; }
.component-chip.sorted-trash   .chip-status { opacity: 1; background: #6b7280;           color: #fff; }
.component-chip.sorted-compost .chip-status { opacity: 1; background: var(--green-mid);  color: #fff; }

/* feedback + next */
.feedback-banner {
  border-radius: 16px;
  padding: 14px 18px;
  font-size: 15px;
  font-weight: 500;
  line-height: 1.55;
  display: none;
  flex-shrink: 0;
}
.feedback-banner.correct { background: var(--green-pale); color: var(--green);  border: 2px solid var(--green-light); }
.feedback-banner.wrong   { background: #fde8e8;           color: #b91c1c;       border: 2px solid #fca5a5; }
.feedback-banner.show    { display: block; }

.next-btn {
  background: var(--green);
  color: #fff;
  border: none;
  border-radius: 100px;
  padding: 18px;
  font-family: var(--fb);
  font-size: 17px;
  font-weight: 700;
  cursor: pointer;
  width: 100%;
  display: none;
  flex-shrink: 0;
  transition: background .15s;
}
.next-btn:active { background: var(--green-mid); }
.next-btn.show   { display: block; }

/* ── BINS ── */
.bins-area {
  background: var(--white);
  border-top: 1.5px solid var(--border);
  padding: 14px 16px max(18px, env(safe-area-inset-bottom));
  flex-shrink: 0;
}

.bins-hint {
  text-align: center;
  font-size: 12px;
  color: var(--gray);
  margin-bottom: 12px;
  font-weight: 500;
  min-height: 16px;
}

.bins-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.bin-btn {
  border: 2px solid var(--border);
  border-radius: 16px;
  background: var(--white);
  padding: 16px 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  transition: all .18s;
}
.bin-btn:active { transform: scale(.94); }

.bin-indicator {
  width: 14px; height: 14px;
  border-radius: 50%;
}
.bin-btn.recycle .bin-indicator { background: var(--blue); }
.bin-btn.trash   .bin-indicator { background: #9ca3af; }
.bin-btn.compost .bin-indicator { background: var(--green-light); }

.bin-name {
  font-size: 13px;
  font-weight: 700;
  letter-spacing: .02em;
}
.bin-btn.recycle { border-color: var(--blue);         background: var(--blue-pale);  }
.bin-btn.recycle .bin-name { color: var(--blue); }
.bin-btn.trash   { border-color: #9ca3af;             background: #f5f5f5; }
.bin-btn.trash   .bin-name { color: #555; }
.bin-btn.compost { border-color: var(--green-light);  background: var(--green-pale); }
.bin-btn.compost .bin-name { color: var(--green-mid); }

.bin-btn.inactive { opacity: .35; pointer-events: none; }

@keyframes binPulse { 0%{transform:scale(1)} 40%{transform:scale(1.08)} 100%{transform:scale(1)} }
.bin-btn.pulse { animation: binPulse .22s ease; }

/* ── RESULTS ── */
#screen-results {
  background: linear-gradient(170deg, var(--green) 0%, var(--green-mid) 100%);
  align-items: center;
  justify-content: center;
  padding: 48px 28px;
  text-align: center;
}

.results-grade {
  font-family: var(--fd);
  font-size: 22px;
  font-weight: 400;
  font-style: italic;
  color: rgba(255,255,255,.7);
  margin-bottom: 4px;
}
.results-title {
  font-family: var(--fd);
  font-size: 40px;
  font-weight: 800;
  color: #fff;
  margin-bottom: 20px;
}
.results-score {
  font-family: var(--fd);
  font-size: 96px;
  font-weight: 800;
  color: var(--amber);
  line-height: 1;
  margin-bottom: 4px;
}
.results-of {
  font-size: 15px;
  color: rgba(255,255,255,.6);
  margin-bottom: 36px;
}

.results-breakdown {
  background: rgba(255,255,255,.10);
  border-radius: 20px;
  padding: 20px 24px;
  width: 100%;
  max-width: 340px;
  margin-bottom: 36px;
}
.breakdown-title {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: .1em;
  text-transform: uppercase;
  color: rgba(255,255,255,.4);
  margin-bottom: 14px;
}
.breakdown-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 9px 0;
  border-bottom: 1px solid rgba(255,255,255,.10);
  font-size: 15px;
}
.breakdown-row:last-child { border: none; }
.bd-left {
  display: flex;
  align-items: center;
  gap: 10px;
  color: rgba(255,255,255,.8);
}
.bd-dot {
  width: 10px; height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}
.bd-dot.recycle { background: #93c5fd; }
.bd-dot.trash   { background: rgba(255,255,255,.5); }
.bd-dot.compost { background: var(--green-pale); }
.bd-right { font-weight: 700; color: var(--amber); }

.play-again-btn {
  background: var(--amber);
  color: var(--green);
  border: none;
  padding: 20px 48px;
  border-radius: 100px;
  font-family: var(--fb);
  font-size: 20px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 8px 32px rgba(233,168,32,.45);
  transition: transform .15s;
}
.play-again-btn:active { transform: scale(.96); }

/* ── TOAST ── */
.toast {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  background: #1c1c1c;
  color: #fff;
  padding: 12px 24px;
  border-radius: 100px;
  font-size: 14px;
  font-weight: 500;
  max-width: 90vw;
  text-align: center;
  z-index: 999;
  box-shadow: 0 4px 24px rgba(0,0,0,.3);
}

/* ── RESPONSIVE ── */
@media (min-width: 480px) {
  .item-name  { font-size: 30px; }
  .bin-name   { font-size: 14px; }
}
@media (min-width: 700px) {
  .game-body, .bins-area {
    max-width: 600px;
    margin-left: auto;
    margin-right: auto;
    width: 100%;
  }
}
</style>
</head>
<body>

<!-- START SCREEN -->
<div id="screen-start" class="screen active">
  <div class="logo">Waste<span>Wise</span></div>
  <p class="tagline">Take it apart. Sort it right.</p>

  <div class="bin-legend">
    <div class="bin-pill recycle"><span class="dot"></span>Recycle</div>
    <div class="bin-pill trash">  <span class="dot"></span>Trash</div>
    <div class="bin-pill compost"><span class="dot"></span>Compost</div>
  </div>

  <button class="start-btn" id="startBtn">Start Sorting</button>
  <p class="start-note" id="startNote">Loading items...</p>
</div>

<!-- GAME SCREEN -->
<div id="screen-game" class="screen">
  <div class="topbar">
    <div class="topbar-logo">Waste<span>Wise</span></div>
    <div class="topbar-right">
      <div class="topbar-prog" id="progressLabel">1 / 10</div>
      <div class="topbar-score">Score <span id="scoreNum">0</span></div>
    </div>
  </div>
  <div class="prog-wrap">
    <div class="prog-fill" id="progressFill" style="width:10%"></div>
  </div>

  <div class="game-body" id="gameBody">

    <div class="item-card">
      <div class="item-tag">Sort this item</div>
      <div class="item-name" id="itemName"></div>
      <div class="item-desc" id="itemDesc"></div>
      <button class="disassemble-btn hidden" id="disassembleBtn"></button>
    </div>

    <div class="components-zone hidden" id="componentsZone">
      <div class="zone-label" id="zoneLabel">Select a piece, then tap a bin below</div>
      <div id="componentsList"></div>
    </div>

    <div class="feedback-banner" id="feedbackBanner"></div>
    <button class="next-btn" id="nextBtn"></button>
  </div>

  <div class="bins-area">
    <div class="bins-hint" id="binsHint">Select a piece above, then tap a bin</div>
    <div class="bins-row">
      <button class="bin-btn recycle" data-bin="recycle">
        <div class="bin-indicator"></div>
        <div class="bin-name">Recycle</div>
      </button>
      <button class="bin-btn trash" data-bin="trash">
        <div class="bin-indicator"></div>
        <div class="bin-name">Trash</div>
      </button>
      <button class="bin-btn compost" data-bin="compost">
        <div class="bin-indicator"></div>
        <div class="bin-name">Compost</div>
      </button>
    </div>
  </div>
</div>

<!-- RESULTS SCREEN -->
<div id="screen-results" class="screen">
  <div class="results-grade"  id="resultsGrade"></div>
  <div class="results-title"  id="resultsTitle"></div>
  <div class="results-score"  id="resultsScore"></div>
  <div class="results-of"     id="resultsOf"></div>
  <div class="results-breakdown">
    <div class="breakdown-title">Breakdown by bin</div>
    <div class="breakdown-row">
      <span class="bd-left"><span class="bd-dot recycle"></span>Recycle</span>
      <span class="bd-right" id="brRecycle">-</span>
    </div>
    <div class="breakdown-row">
      <span class="bd-left"><span class="bd-dot trash"></span>Trash</span>
      <span class="bd-right" id="brTrash">-</span>
    </div>
    <div class="breakdown-row">
      <span class="bd-left"><span class="bd-dot compost"></span>Compost</span>
      <span class="bd-right" id="brCompost">-</span>
    </div>
  </div>
  <button class="play-again-btn" id="playAgainBtn">Play Again</button>
</div>

<div class="toast hidden" id="toast"></div>

<script>
let allItems = [], gameItems = [], currentIdx = 0;
let selectedCompId = null, sortedMap = {}, score = 0;
let totalParts = 0, correctParts = 0;
let catStats = { recycle:{c:0,t:0}, trash:{c:0,t:0}, compost:{c:0,t:0} };

document.addEventListener("DOMContentLoaded", async () => {
  try {
    const res = await fetch("/api/items");
    allItems  = await res.json();
    document.getElementById("startNote").textContent =
      allItems.length + " items  |  disassemble  |  sort each piece";
  } catch(e) {
    showToast("Could not load items. Is Flask running?");
  }
  document.getElementById("startBtn").addEventListener("click", startGame);
  document.getElementById("playAgainBtn").addEventListener("click", startGame);
  document.getElementById("disassembleBtn").addEventListener("click", doDisassemble);
  document.getElementById("nextBtn").addEventListener("click", nextItem);
  document.querySelectorAll(".bin-btn").forEach(b =>
    b.addEventListener("click", () => sortSelected(b.dataset.bin))
  );
});

function shuffle(a) { return [...a].sort(() => Math.random() - 0.5); }

function startGame() {
  gameItems    = shuffle(allItems).slice(0, 10);
  currentIdx   = 0; score = 0; totalParts = 0; correctParts = 0;
  catStats     = { recycle:{c:0,t:0}, trash:{c:0,t:0}, compost:{c:0,t:0} };
  showScreen("game");
  loadItem();
}

function loadItem() {
  const item = gameItems[currentIdx];
  selectedCompId = null; sortedMap = {};

  document.getElementById("progressFill").style.width =
    (Math.round((currentIdx / 10) * 100) + 10) + "%";
  document.getElementById("progressLabel").textContent = (currentIdx + 1) + " / 10";
  document.getElementById("scoreNum").textContent = score;
  document.getElementById("itemName").textContent  = item.name;
  document.getElementById("itemDesc").textContent  = item.description;

  const btn = document.getElementById("disassembleBtn");
  if (item.disassemble) {
    btn.classList.remove("hidden");
    btn.textContent = item.btn_label;
  } else {
    btn.classList.add("hidden");
  }

  document.getElementById("componentsZone").classList.add("hidden");
  document.getElementById("componentsList").innerHTML = "";
  document.getElementById("feedbackBanner").className = "feedback-banner";
  document.getElementById("nextBtn").classList.remove("show");
  document.getElementById("binsHint").textContent = "Select a piece above, then tap a bin";
  setBinsActive(false);
  document.getElementById("gameBody").scrollTop = 0;

  if (!item.disassemble) { renderComponents(item); setBinsActive(true); }
}

function doDisassemble() {
  const item = gameItems[currentIdx];
  document.getElementById("disassembleBtn").classList.add("hidden");
  renderComponents(item);
  setBinsActive(true);
  setTimeout(() =>
    document.getElementById("componentsZone")
      .scrollIntoView({ behavior: "smooth", block: "nearest" }), 120);
}

function renderComponents(item) {
  const single = item.components.length === 1;
  document.getElementById("zoneLabel").textContent =
    single ? "Tap the correct bin below" : "Select a piece, then tap a bin below";

  document.getElementById("componentsList").innerHTML = item.components.map(c => `
    <div class="component-chip" id="chip-${c.id}" data-id="${c.id}">
      <div class="chip-left">
        <div class="chip-name">${c.name}</div>
      </div>
      <div class="chip-status" id="status-${c.id}"></div>
    </div>`).join("");

  document.querySelectorAll(".component-chip").forEach(ch =>
    ch.addEventListener("click", () => selectComponent(Number(ch.dataset.id)))
  );
  document.getElementById("componentsZone").classList.remove("hidden");
}

function selectComponent(id) {
  if (sortedMap[id] !== undefined) return;
  if (selectedCompId && selectedCompId !== id)
    document.getElementById("chip-" + selectedCompId)?.classList.remove("selected");
  selectedCompId = id;
  document.getElementById("chip-" + id).classList.add("selected");
  const comp = gameItems[currentIdx].components.find(c => c.id === id);
  document.getElementById("binsHint").textContent = 'Now tap the bin for "' + comp.name + '"';
}

async function sortSelected(binChoice) {
  if (!selectedCompId) {
    document.querySelectorAll(".bin-btn").forEach(b => {
      b.classList.add("pulse");
      setTimeout(() => b.classList.remove("pulse"), 300);
    });
    document.getElementById("binsHint").textContent = "Select a piece above first";
    return;
  }

  const compId = selectedCompId; selectedCompId = null;
  let result;
  try {
    const res = await fetch("/api/sort", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ component_id: compId, chosen_bin: binChoice }),
    });
    result = await res.json();
  } catch(e) { showToast("Network error."); return; }

  sortedMap[compId] = binChoice;
  const chip = document.getElementById("chip-" + compId);
  chip.classList.remove("selected");
  chip.classList.add("sorted-" + binChoice);
  chip.onclick = null;
  const labels = { recycle: "Recycle", trash: "Trash", compost: "Compost" };
  document.getElementById("status-" + compId).textContent = labels[binChoice];

  totalParts++;
  catStats[result.correct_bin].t++;
  if (result.correct) {
    correctParts++;
    catStats[result.correct_bin].c++;
    score++;
  } else {
    chip.classList.add("wrong-flash");
    setTimeout(() => chip.classList.remove("wrong-flash"), 500);
  }

  document.getElementById("scoreNum").textContent = score;
  document.getElementById("binsHint").textContent = "Select a piece above, then tap a bin";
  const binEl = document.querySelector(`.bin-btn[data-bin="${binChoice}"]`);
  binEl.classList.add("pulse");
  setTimeout(() => binEl.classList.remove("pulse"), 300);

  const item = gameItems[currentIdx];
  if (item.components.every(c => sortedMap[c.id] !== undefined)) {
    setBinsActive(false);
    const wrong = item.components.filter(c => sortedMap[c.id] !== c.correct_bin);
    const banner = document.getElementById("feedbackBanner");
    if (wrong.length === 0) {
      banner.className = "feedback-banner correct show";
      banner.innerHTML = "<strong>Correct!</strong> Every piece sorted correctly.";
    } else {
      const fixes = wrong.map(c => {
        const l = { recycle: "Recycle", trash: "Trash", compost: "Compost" }[c.correct_bin];
        return "<strong>" + c.name + "</strong> goes in " + l;
      }).join("<br>");
      banner.className = "feedback-banner wrong show";
      banner.innerHTML = "Not quite — here is the fix:<br>" + fixes;
    }
    const nb = document.getElementById("nextBtn");
    nb.textContent = currentIdx >= 9 ? "See Results" : "Next Item";
    nb.classList.add("show");
    setTimeout(() =>
      banner.scrollIntoView({ behavior: "smooth", block: "nearest" }), 120);
  }
}

function nextItem() {
  currentIdx++;
  if (currentIdx >= 10) { showResults(); return; }
  loadItem();
  document.getElementById("gameBody").scrollTop = 0;
}

function showResults() {
  document.getElementById("progressFill").style.width = "100%";
  const pct  = Math.round((correctParts / Math.max(totalParts, 1)) * 100);
  const tier = Math.min(5, Math.floor(pct / 20));
  const grades = ["Needs Work", "Needs Work", "Good Effort", "Getting There", "Great Job", "Perfect"];
  const titles = ["Keep Learning", "Keep Learning", "Good Effort!", "Getting There!", "Great Job!", "Perfect Score!"];
  document.getElementById("resultsGrade").textContent  = grades[tier];
  document.getElementById("resultsTitle").textContent  = titles[tier];
  document.getElementById("resultsScore").textContent  = correctParts;
  document.getElementById("resultsOf").textContent     =
    "out of " + totalParts + " pieces sorted correctly";
  const fmt = k => catStats[k].t ? catStats[k].c + " / " + catStats[k].t : "-";
  document.getElementById("brRecycle").textContent = fmt("recycle");
  document.getElementById("brTrash").textContent   = fmt("trash");
  document.getElementById("brCompost").textContent = fmt("compost");
  showScreen("results");
}

function showScreen(id) {
  document.querySelectorAll(".screen").forEach(s => s.classList.remove("active"));
  document.getElementById("screen-" + id).classList.add("active");
  window.scrollTo(0, 0);
}

function setBinsActive(on) {
  document.querySelectorAll(".bin-btn").forEach(b => b.classList.toggle("inactive", !on));
}

function showToast(msg) {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.classList.remove("hidden");
  setTimeout(() => t.classList.add("hidden"), 3500);
}
</script>
</body>
</html>"""


# ======================================================================
# DATABASE HELPERS
# ======================================================================

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

@app.teardown_appcontext
def close_db(exc=None):
    db = g.pop("db", None)
    if db: db.close()

def init_db():
    if not os.path.exists(DB_PATH):
        with app.app_context():
            db = get_db()
            db.executescript(SCHEMA + SEED)
            db.commit()
            print("Database created and seeded.")

def get_session_id():
    if "sid" not in session:
        session["sid"] = str(uuid.uuid4())
    return session["sid"]


# ======================================================================
# ROUTES
# ======================================================================

@app.route("/")
def index():
    return render_template_string(PAGE)


@app.route("/api/items")
def api_items():
    db    = get_db()
    items = db.execute("SELECT * FROM items ORDER BY id").fetchall()
    result = []
    for item in items:
        comps = db.execute(
            "SELECT id, slug, name, correct_bin FROM components WHERE item_id=? ORDER BY id",
            (item["id"],)
        ).fetchall()
        result.append({
            "id":          item["id"],
            "name":        item["name"],
            "description": item["description"],
            "disassemble": bool(item["disassemble"]),
            "btn_label":   item["btn_label"],
            "components":  [dict(c) for c in comps],
        })
    return jsonify(result)


@app.route("/api/sort", methods=["POST"])
def api_sort():
    data         = request.get_json(silent=True) or {}
    component_id = data.get("component_id")
    chosen_bin   = data.get("chosen_bin")

    if not component_id or chosen_bin not in ("recycle", "trash", "compost"):
        return jsonify({"error": "Invalid input"}), 400

    db   = get_db()
    comp = db.execute(
        "SELECT id, correct_bin FROM components WHERE id=?", (component_id,)
    ).fetchone()
    if not comp:
        return jsonify({"error": "Not found"}), 404

    is_correct = int(chosen_bin == comp["correct_bin"])
    db.execute(
        "INSERT INTO sort_attempts (session_id, component_id, chosen_bin, is_correct) "
        "VALUES (?, ?, ?, ?)",
        (get_session_id(), component_id, chosen_bin, is_correct)
    )
    db.commit()
    return jsonify({"correct": bool(is_correct), "correct_bin": comp["correct_bin"]})


@app.route("/api/stats")
def api_stats():
    sid = get_session_id()
    db  = get_db()
    row = db.execute(
        "SELECT COUNT(*) AS total, SUM(is_correct) AS correct "
        "FROM sort_attempts WHERE session_id=?", (sid,)
    ).fetchone()
    total   = row["total"]   or 0
    correct = row["correct"] or 0
    rows = db.execute(
        """SELECT c.correct_bin AS bin,
                  COUNT(*) AS attempts,
                  SUM(a.is_correct) AS correct
           FROM sort_attempts a
           JOIN components c ON c.id = a.component_id
           WHERE a.session_id = ?
           GROUP BY c.correct_bin""", (sid,)
    ).fetchall()
    by_bin = {b: {"attempts": 0, "correct": 0} for b in ("recycle", "trash", "compost")}
    for r in rows:
        by_bin[r["bin"]] = {"attempts": r["attempts"], "correct": r["correct"] or 0}
    return jsonify({
        "total_attempts": total,
        "correct":        correct,
        "accuracy_pct":   round(correct / total * 100) if total else 0,
        "by_bin":         by_bin,
    })


# ======================================================================
# START
# ======================================================================

if __name__ == "__main__":
    init_db()
    print("\n  WasteWise is running!")
    print("  Local:   http://localhost:5000")
    print("  Network: find your IP with 'ipconfig' (Windows) or 'ifconfig' (Mac/Linux)\n")
    app.run(debug=True, host="0.0.0.0", port=5000)