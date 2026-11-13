
# Book World — Pipeline ETL et API REST

## 1. Présentation du projet

Book World est un projet de traitement et d'analyse de données de ventes de livres.

L'objectif est de construire un pipeline ETL (Extract, Transform, Load) permettant de collecter des données provenant de plusieurs sources, de les nettoyer, de les enrichir et de les enregistrer dans une base de données relationnelle SQLite.

Une API REST développée avec Flask permet ensuite de consulter les indicateurs de ventes.

## 2. Technologies utilisées

- Python : développement du pipeline ETL
- Pandas : nettoyage, jointures et agrégations
- SQLite : stockage des données
- Requests : récupération des données via API et HTTP
- BeautifulSoup : scraping du catalogue de livres
- Flask : création de l'API REST
- python-dotenv : gestion de la clé API
- Git et GitHub : versionnement du projet

## 3. Sources de données

Le projet utilise quatre sources :

| Source | Fichier ou service | Données |
|---|---|---|
| CSV | sales_raw.csv | Ventes brutes |
| SQLite | bookworld_reference.db | Pays, canaux et règles de catégories |
| Web scraping | books.toscrape.com | Titres et prix des livres |
| API externe | Frankfurter | Taux de change GBP/EUR |

Le scraping récupère les livres de la première page du catalogue Books to Scrape.

Le taux de change permet de convertir les chiffres d'affaires de GBP vers EUR.

## 4. Fonctionnement du pipeline ETL

### Extract — Extraction

Le fichier pipeline.py extrait :

- Les ventes du fichier CSV
- Les pays, canaux et catégories depuis SQLite
- Les titres et prix des livres depuis Books to Scrape
- Le taux de change GBP/EUR depuis Frankfurter

### Transform — Transformation

Le pipeline réalise :

1. Le contrôle des doublons
2. La vérification des valeurs manquantes
3. La validation des quantités et des remises
4. La vérification du format des dates
5. La vérification des codes pays
6. L'enrichissement des ventes avec les prix des livres
7. Le calcul du chiffre d'affaires en GBP
8. La conversion du chiffre d'affaires en EUR
9. La suppression des noms et prénoms dans les tables finales
10. L'agrégation des ventes par pays

Formule du chiffre d'affaires :

revenue_gbp = quantity × price_gbp × (1 - discount_rate)

revenue_eur = revenue_gbp × taux_GBP_EUR

Les montants sont calculés avec les prix disponibles sur le site et le taux de change récupéré lors de l'exécution. Ils représentent donc des estimations pédagogiques, et non des montants historiques certifiés.

### Load — Chargement

Les données sont enregistrées dans bookworld_final.db.

La base finale contient quatre tables relationnelles.

## 5. Structure de la base de données

| Table | Description |
|---|---|
| countries | Référentiel des pays |
| books | Catalogue des livres et leurs prix |
| sales_clean | Ventes nettoyées et enrichies |
| sales_by_country | Indicateurs agrégés par pays |

### Relations entre les tables

- sales_clean.book_id référence books.book_id
- sales_clean.country_code référence countries.country_code
- sales_by_country.country_code référence countries.country_code

Le fichier schema_final.sql contient la définition des tables, des clés primaires et des clés étrangères.

### Exemple de jointure SQL

```sql
SELECT
    s.order_id,
    b.title,
    c.country_name,
    s.quantity,
    s.revenue_eur
FROM sales_clean s
JOIN books b
    ON s.book_id = b.book_id
JOIN countries c
    ON s.country_code = c.country_code;
```

Cette requête permet d'associer les ventes aux titres des livres et aux noms des pays.

Le fichier queries.sql contient également des requêtes d'analyse et d'agrégation.

## 6. Résultats du traitement

Lors des tests du projet :

| Indicateur | Résultat |
|---|---|
| Ventes traitées | 240 |
| Livres du catalogue | 20 |
| Pays du référentiel final | 11 |
| Pays ayant des ventes | 8 |
| Doublons exacts détectés | 0 |
| Quantités invalides | 0 |
| Remises invalides | 0 |
| Dates invalides | 0 |
| Ventes sans correspondance de pays | 0 |
| Ventes sans correspondance de prix | 0 |

Ces résultats correspondent au jeu de données utilisé pour le projet.

## 7. API REST Flask

Le fichier api.py expose quatre endpoints protégés par une clé API.

| Méthode | Endpoint | Description |
|---|---|---|
| GET | /sales_by_country | Afficher les ventes par pays |
| GET | /sales_by_country/FR | Afficher les ventes pour un pays |
| GET | /kpis | Afficher les indicateurs globaux |
| GET | /top_countries | Classer les pays selon leur chiffre d'affaires |

La clé API est transmise dans l'en-tête HTTP X-API-Key.

Une requête sans clé valide retourne une erreur HTTP 401.

## 8. Installation et exécution

### Prérequis

- Python 3
- pip
- SQLite

### Installation

Cloner le dépôt GitHub, puis accéder au dossier du projet.

Créer et activer un environnement virtuel :

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Installer les dépendances :

```bash
pip install -r requirements.txt
```

### Configuration de la clé API

Créer un fichier .env à la racine du projet :

```env
API_KEY=remplacer_par_une_cle_secrete
```

Le fichier .env ne doit pas être publié sur GitHub.

### Exécuter le pipeline

```bash
python pipeline.py
```

Le pipeline extrait, transforme et charge les données dans bookworld_final.db.

### Démarrer l'API

```bash
python api.py
```

L'API est accessible localement sur :

http://127.0.0.1:5000

### Tester un endpoint sous Ubuntu

```bash
API_KEY=$(grep '^API_KEY=' .env | cut -d= -f2-)

curl -H "X-API-Key: $API_KEY" \
http://127.0.0.1:5000/kpis
```

## 9. Traitement des données personnelles

Le fichier source sales_raw.csv contient des champs de noms et de prénoms.

Ces informations ne sont pas nécessaires au calcul des indicateurs.

Le pipeline ne les conserve donc pas dans les tables finales :

- countries
- books
- sales_clean
- sales_by_country

L'API expose des indicateurs agrégés et non les noms et prénoms des clients.

Cette démarche applique le principe de minimisation des données.

Attention : l'exclusion des données personnelles de la base finale ne garantit pas, à elle seule, la conformité RGPD. Les données sources doivent également être gérées conformément aux règles applicables.

## 10. Contrôles et sécurité

Le projet comprend :

- Vérification de la qualité des données
- Contrôle des identifiants et des correspondances
- Vérification des clés étrangères SQLite
- Jointures contrôlées avec Pandas
- Authentification de l'API par clé
- Configuration Flask avec debug=False
- Stockage de la clé API dans un fichier .env non versionné

## 11. Organisation du projet

```text
book-world/
|
|-- pipeline.py
|-- api.py
|-- sales_raw.csv
|-- bookworld_reference.db
|-- bookworld_final.db
|-- schema_final.sql
|-- queries.sql
|-- requirements.txt
|-- README.md
|-- .gitignore
```

Les fichiers locaux de sauvegarde et de test ne sont pas nécessaires à l'utilisation du projet.

## 12. Conclusion

Le projet Book World met en œuvre une chaîne complète de traitement de données :

Extraction → Contrôle qualité → Transformation → Enrichissement → Agrégation → Stockage SQLite → API REST

Il permet de démontrer des compétences en Python, SQL, modélisation relationnelle, intégration de données, développement d'API et contrôle de qualité.

Le projet constitue un cas pratique de préparation à la certification RNCP en Data Analysis.

