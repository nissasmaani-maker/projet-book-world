-- 1. Extraire tous les pays
SELECT *
FROM countries;


-- 2. Extraire uniquement les pays actifs
-- Requête avec filtre
SELECT *
FROM countries
WHERE is_active = 1;


-- 3. Extraire les canaux de vente actifs
SELECT *
FROM channels
WHERE is_active = 1;


-- 4. Enrichir les catégories avec les canaux
-- Requête avec jointure
SELECT
    c.category_name,
    c.margin_rate,
    c.strategic_flag,
    ch.channel_name,
    ch.acquisition_cost_gbp
FROM category_rules AS c
LEFT JOIN channels AS ch
    ON c.default_channel_code = ch.channel_code;
