-- WasteWise database schema and seed data
-- Run via app.py on first launch (auto-detected)

DROP TABLE IF EXISTS components;
DROP TABLE IF EXISTS items;

CREATE TABLE items (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    name              TEXT    NOT NULL,
    description       TEXT    NOT NULL,
    needs_disassembly INTEGER NOT NULL DEFAULT 0,  -- 0 = sort as-is, 1 = take apart first
    disassemble_label TEXT                          -- button label shown to user
);

CREATE TABLE components (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id    INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    name       TEXT    NOT NULL,
    bin        TEXT    NOT NULL CHECK(bin IN ('recycle', 'trash', 'compost')),
    sort_order INTEGER NOT NULL DEFAULT 0           -- display order within item
);

-- ── Items ─────────────────────────────────────────────────────────────────────

INSERT INTO items (name, description, needs_disassembly, disassemble_label) VALUES
  ('Coffee Cup and Lid',
   'A paper coffee cup with a plastic lid and a cardboard sleeve — three different materials.',
   1, 'Take It Apart'),

  ('Pizza Box with Leftover Crust',
   'A cardboard pizza box with a greasy bottom half and a leftover crust inside.',
   1, 'Take It Apart'),

  ('Plastic Cup and Paper Straw',
   'A clear plastic drink cup paired with a paper straw.',
   1, 'Separate the Straw'),

  ('Takeout Container with Food',
   'A plastic clamshell container with leftover noodles inside.',
   1, 'Remove the Food'),

  ('Banana with Produce Sticker',
   'A banana peel with a small plastic PLU sticker attached.',
   1, 'Peel Off the Sticker'),

  ('Dry Newspaper',
   'A clean, dry newspaper with no food stains or moisture.',
   0, NULL),

  ('Salad Container and Plastic Fork',
   'A clear plastic salad container with leftover dressing and a disposable fork.',
   1, 'Separate the Parts'),

  ('Cardboard Box with Packing Tape',
   'A shipping box with plastic packing tape strips still attached.',
   1, 'Remove the Tape'),

  ('Apple Core in a Paper Bag',
   'An apple core sitting inside a clean paper lunch bag.',
   1, 'Remove the Apple'),

  ('Yogurt Cup with Foil Lid',
   'A plastic yogurt cup with a peelable foil lid and leftover yogurt inside.',
   1, 'Peel the Lid and Scrape');

-- ── Components ────────────────────────────────────────────────────────────────
-- item_id values match the insertion order of the items above (1–10)

INSERT INTO components (item_id, name, bin, sort_order) VALUES
  -- 1. Coffee Cup and Lid
  (1, 'Plastic Lid',              'trash',   1),
  (1, 'Cardboard Sleeve',         'recycle', 2),
  (1, 'Paper Cup Body',           'trash',   3),

  -- 2. Pizza Box with Leftover Crust
  (2, 'Leftover Crust',           'compost', 1),
  (2, 'Clean Box Top Half',       'recycle', 2),
  (2, 'Greasy Box Bottom Half',   'trash',   3),

  -- 3. Plastic Cup and Paper Straw
  (3, 'Clear Plastic Cup',        'recycle', 1),
  (3, 'Paper Straw',              'compost', 2),

  -- 4. Takeout Container with Food
  (4, 'Leftover Noodles',         'compost', 1),
  (4, 'Rinsed Plastic Clamshell', 'recycle', 2),

  -- 5. Banana with Produce Sticker
  (5, 'Plastic Produce Sticker',  'trash',   1),
  (5, 'Banana Peel',              'compost', 2),

  -- 6. Dry Newspaper
  (6, 'Dry Newspaper',            'recycle', 1),

  -- 7. Salad Container and Plastic Fork
  (7, 'Leftover Dressing',        'compost', 1),
  (7, 'Plastic Fork',             'trash',   2),
  (7, 'Rinsed Plastic Container', 'recycle', 3),

  -- 8. Cardboard Box with Packing Tape
  (8, 'Plastic Packing Tape',     'trash',   1),
  (8, 'Flattened Cardboard',      'recycle', 2),

  -- 9. Apple Core in a Paper Bag
  (9, 'Apple Core',               'compost', 1),
  (9, 'Clean Paper Bag',          'recycle', 2),

  -- 10. Yogurt Cup with Foil Lid
  (10, 'Leftover Yogurt',         'compost', 1),
  (10, 'Foil Lid',                'recycle', 2),
  (10, 'Plastic Cup',             'recycle', 3);