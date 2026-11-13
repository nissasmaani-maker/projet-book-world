-- 1. Afficher les ventes avec les titres des livres et les pays
SELECT
    s.order_id,
    b.title,
    c.country_name,
    s.quantity,
    s.revenue_eur
FROM sales_clean s
JOIN books b ON s.book_id = b.book_id
JOIN countries c ON s.country_code = c.country_code;


-- 2. Calculer le chiffre d'affaires par pays
SELECT
    c.country_name,
    COUNT(DISTINCT s.order_id) AS total_orders,
    SUM(s.revenue_eur) AS total_revenue_eur
FROM sales_clean s
JOIN countries c ON s.country_code = c.country_code
GROUP BY c.country_name
ORDER BY total_revenue_eur DESC;


-- 3. Afficher les 5 livres qui génèrent le plus de CA
SELECT
    b.title,
    SUM(s.quantity) AS total_quantity,
    ROUND(SUM(s.revenue_eur), 2) AS total_revenue_eur
FROM sales_clean s
JOIN books b ON s.book_id = b.book_id
GROUP BY b.book_id, b.title
ORDER BY total_revenue_eur DESC
LIMIT 5;


-- 4. Comparer les chiffres d'affaires calculés et agrégés
SELECT
    c.country_name,
    ROUND(SUM(s.revenue_eur), 2) AS ca_calcule,
    a.total_revenue_eur AS ca_agrege
FROM sales_clean s
JOIN countries c ON s.country_code = c.country_code
JOIN sales_by_country a ON c.country_code = a.country_code
GROUP BY c.country_code, c.country_name, a.total_revenue_eur;
