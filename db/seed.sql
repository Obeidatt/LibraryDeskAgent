--------------------------------------------------
-- SEED DATA
--------------------------------------------------

-- 10 books
INSERT INTO books (isbn, title, author, price, stock) VALUES
('978000000001', 'Introduction to AI', 'John Smith', 25.99, 5),
('978000000002', 'Deep Learning Basics', 'Jane Doe', 39.99, 3),
('978000000003', 'Python for Data Science', 'Alex Brown', 29.99, 8),
('978000000004', 'Machine Learning 101', 'Sara Lee', 34.50, 2),
('978000000005', 'Databases Made Easy', 'Michael Green', 22.00, 6),
('978000000006', 'Algorithms in Practice', 'Emily White', 27.75, 4),
('978000000007', 'Statistics for ML', 'Robert Black', 31.20, 1),
('978000000008', 'NLP in Action', 'Laura Grey', 30.00, 7),
('978000000009', 'Computer Vision Guide', 'Chris Blue', 33.40, 2),
('978000000010', 'Recommender Systems', 'Olivia Clark', 28.60, 9);

-- 6 customers
INSERT INTO customers (name, email) VALUES
('Omar Ahmad', 'omar@example.com'),
('Momen Ali', 'momen@example.com'),
('Anas Obeidat', 'obeiidattt@gmail.com'),
('Lina Hasan', 'lina@example.com'),
('Sara Khalid', 'sara@example.com'),
('Yousef Naser', 'yousef@example.com');

-- 4 orders
INSERT INTO orders (customer_id, created_at, status) VALUES
(1, '2025-01-01T10:00:00', 'completed'),
(2, '2025-01-02T11:30:00', 'completed'),
(3, '2025-01-03T15:45:00', 'pending'),
(3, '2025-01-04T09:20:00', 'completed');

-- Order items
INSERT INTO order_items (order_id, isbn, qty) VALUES
(1, '978000000001', 1),
(1, '978000000003', 2),
(2, '978000000004', 1),
(2, '978000000005', 1),
(3, '978000000002', 1),
(3, '978000000008', 1),
(4, '978000000009', 2),
(4, '978000000010', 1);
