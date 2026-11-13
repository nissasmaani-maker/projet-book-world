-- Base finale Book World
-- Structure relationnelle sans données personnelles

-- 1. Référentiel des pays
CREATE TABLE IF NOT EXISTS countries (
    country_code TEXT PRIMARY KEY,
    country_name TEXT NOT NULL
);

-- 2. Catalogue des livres
CREATE TABLE IF NOT EXISTS books (
    book_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    price_gbp REAL NOT NULL
);

-- 3. Ventes nettoyées
CREATE TABLE IF NOT EXISTS sales_clean (
    sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT NOT NULL,
    order_date TEXT,
    book_id TEXT NOT NULL,
    country_code TEXT NOT NULL,
    channel_code TEXT,
    quantity INTEGER NOT NULL,
    discount_rate REAL,
    revenue_gbp REAL,
    revenue_eur REAL,

    FOREIGN KEY (book_id) REFERENCES books(book_id),
    FOREIGN KEY (country_code) REFERENCES countries(country_code)
);

-- 4. Agrégation des ventes par pays
CREATE TABLE IF NOT EXISTS sales_by_country (
    country_code TEXT PRIMARY KEY,
    country_name TEXT NOT NULL,
    total_orders INTEGER NOT NULL,
    total_quantity INTEGER NOT NULL,
    total_revenue_gbp REAL NOT NULL,
    total_revenue_eur REAL NOT NULL,

    FOREIGN KEY (country_code) REFERENCES countries(country_code)
);
