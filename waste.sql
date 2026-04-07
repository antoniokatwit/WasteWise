-- ============================================================
-- WasteWise Database Schema + Seed Data (CLEANED)
-- ============================================================

DROP TABLE IF EXISTS sort_attempts;
DROP TABLE IF EXISTS components;
DROP TABLE IF EXISTS items;

-- ── ITEMS ──────────────────────────────────────────────────
CREATE TABLE items (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT    NOT NULL,
    description   TEXT    NOT NULL,
    disassemble   INTEGER NOT NULL DEFAULT 1,
    btn_label     TEXT    NOT NULL DEFAULT 'Take it apart'
);

-- ── COMPONENTS ─────────────────────────────────────────────
CREATE TABLE components (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id     INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    slug        TEXT    NOT NULL,
    name        TEXT    NOT NULL,
    correct_bin TEXT    NOT NULL CHECK(correct_bin IN ('recycle','trash','compost'))
);

-- ── SORT_ATTEMPTS ──────────────────────────────────────────
CREATE TABLE sort_attempts (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id    TEXT    NOT NULL,
    component_id  INTEGER NOT NULL REFERENCES components(id),
    chosen_bin    TEXT    NOT NULL CHECK(chosen_bin IN ('recycle','trash','compost')),
    is_correct    INTEGER NOT NULL,
    attempted_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_attempts_session ON sort_attempts(session_id);

-- ============================================================
-- SEED — 14 items
-- ============================================================

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

-- ── COMPONENTS ─────────────────────────────────────────────

INSERT INTO components (item_id, slug, name, correct_bin) VALUES
-- 1
(1, 'straw', 'Plastic straw', 'trash'),
(1, 'lid',   'Plastic lid', 'trash'),
(1, 'cup',   'Clear plastic cup', 'recycle'),

-- 2
(2, 'bottle', 'Rinsed plastic bottle', 'recycle'),
(2, 'liquid', 'Any remaining liquid', 'compost'),

-- 3
(3, 'yogurt', 'Leftover yogurt', 'compost'),
(3, 'foil',   'Foil lid (rinsed)', 'recycle'),
(3, 'cup',    'Rinsed plastic cup', 'recycle'),

-- 4
(4, 'sticker', 'Produce sticker', 'trash'),
(4, 'peel',    'Banana peel', 'compost'),

-- 5
(5, 'sticker', 'Produce sticker', 'trash'),
(5, 'peels',   'Orange peels', 'compost'),

-- 6
(6, 'bag', 'Chip bag', 'trash'),

-- 7
(7, 'paper', 'Clean sheet of paper', 'recycle'),

-- 8
(8, 'towel', 'Used paper towel', 'trash'),

-- 9
(9, 'bag', 'Plastic shopping bag', 'trash'),

-- 10
(10, 'crumbs', 'Food crumbs inside', 'compost'),
(10, 'bag',    'Empty Ziploc bag', 'trash'),

-- 11
(11, 'bottle', 'Glass bottle', 'recycle'),

-- 12
(12, 'can', 'Aluminum can', 'recycle'),

-- 13
(13, 'wrapper', 'Candy wrapper', 'trash'),

-- 14
(14, 'bones', 'Bones', 'trash');