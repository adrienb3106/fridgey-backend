USE fridgey;

-- ---------- USERS ----------
INSERT INTO users (name, email) VALUES
('Alice', 'alice@example.com'),
('Bob', 'bob@example.com'),
('Charlie', 'charlie@example.com');

-- ---------- GROUPS ----------
INSERT INTO groups (name) VALUES
('Famille'),
('Coloc'),
('Amis');

-- ---------- USER_GROUPS ----------
INSERT INTO user_groups (user_id, group_id, role) VALUES
(1, 1, 'admin'),   -- Alice admin Famille
(2, 1, 'member'),  -- Bob membre Famille
(2, 2, 'admin'),   -- Bob admin Coloc
(3, 3, 'member');  -- Charlie membre Amis

-- ---------- ITEMS ----------
INSERT INTO items (name, is_food, unit) VALUES
('Beurre', TRUE, 'g'),
('Lait', TRUE, 'L'),
('Pâtes', TRUE, 'kg'),
('Lessive', FALSE, 'L'),
('Papier toilette', FALSE, 'unités');

-- ---------- STOCKS ----------
INSERT INTO stocks (item_id, user_id, group_id, expiration_date, initial_quantity, remaining_quantity, lot_count)
VALUES
(1, 1, NULL, '2025-10-01', 250.00, 200.00, 1), -- Beurre d'Alice
(2, NULL, 1, '2025-09-20', 6.00, 4.00, 1),     -- Lait du groupe Famille
(3, 2, 2, '2026-01-01', 2.00, 1.50, 1),        -- Pâtes de Bob
(4, NULL, 2, NULL, 3.00, 3.00, 1),             -- Lessive du groupe Coloc
(5, 3, 3, NULL, 24.00, 20.00, 1);              -- PQ de Charlie (Amis)

-- ---------- STOCK_MOVEMENTS ----------
INSERT INTO stock_movements (stock_id, change_quantity, note) VALUES
(1, 250.00, 'Stock initial'),
(1, -50.00, 'Alice a utilisé 50g de beurre'),
(2, 6.00, 'Stock initial'),
(2, -2.00, 'Famille a bu 2L de lait'),
(3, 2.00, 'Stock initial'),
(4, 3.00, 'Stock initial'),
(5, 24.00, 'Stock initial'),
(5, -4.00, 'Charlie a utilisé 4 rouleaux');
