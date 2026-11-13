
import pandas as pd
import sqlite3
import requests
from bs4 import BeautifulSoup


# 1. Extraire les ventes CSV
def extraire_ventes():
    ventes = pd.read_csv("sales_raw.csv", sep=";")
    print("Ventes :", len(ventes), "lignes")
    return ventes


# 2. Vérifier la qualité des données
def verifier_qualite(ventes):
    print("\nContrôle qualité :")
    print("Doublons exacts :", ventes.duplicated().sum())
    print("Valeurs manquantes :")
    print(ventes.isnull().sum())

    print("Quantités invalides :", (ventes["quantity"] <= 0).sum())

    print("Remises invalides :", (
        (ventes["discount_rate"] < 0) |
        (ventes["discount_rate"] > 1)
    ).sum())

    dates = pd.to_datetime(
        ventes["order_date"],
        format="%d/%m/%Y",
        errors="coerce"
    )

    print("Dates invalides :", dates.isna().sum())

    if ventes.duplicated().any():
        raise ValueError("Doublons détectés")

    if ventes.isnull().any().any():
        raise ValueError("Valeurs manquantes détectées")

    if (ventes["quantity"] <= 0).any():
        raise ValueError("Quantités invalides")

    if ((ventes["discount_rate"] < 0) |
        (ventes["discount_rate"] > 1)).any():
        raise ValueError("Remises invalides")

    if dates.isna().any():
        raise ValueError("Dates invalides")


# 3. Extraire les référentiels SQLite
def extraire_referentiels():
    with sqlite3.connect("bookworld_reference.db") as connexion:
        pays = pd.read_sql("SELECT * FROM countries", connexion)

        canaux = pd.read_sql(
            "SELECT * FROM channels WHERE is_active = 1",
            connexion
        )

        categories = pd.read_sql(
            "SELECT * FROM category_rules",
            connexion
        )

    # Ajouter les Pays-Bas s'ils sont absents
    if "NL" not in pays["country_code"].values:
        pays = pd.concat([
            pays,
            pd.DataFrame([{
                "country_code": "NL",
                "country_name": "Netherlands"
            }])
        ], ignore_index=True)

    print("Pays :", len(pays))
    print("Canaux :", len(canaux))
    print("Catégories :", len(categories))

    return pays, canaux, categories


# 4. Vérifier les pays
def verifier_pays(ventes, pays):
    manquants = ventes[
        ~ventes["country_code"].isin(pays["country_code"])
    ]

    print("Ventes sans pays :", len(manquants))

    if len(manquants) > 0:
        raise ValueError("Certains pays sont inconnus")


# 5. Scraper le catalogue
def extraire_catalogue():
    url = "https://books.toscrape.com/"

    reponse = requests.get(url, timeout=10)
    reponse.raise_for_status()

    soup = BeautifulSoup(reponse.content, "html.parser")
    livres = []

    for livre in soup.select("article.product_pod"):
        titre = livre.select_one("h3 a")["title"]
        prix = livre.select_one("p.price_color").text

        livres.append({
            "title": titre,
            "price_gbp": float(
                prix.replace("Â", "").replace("£", "").strip()
            )
        })

    if not livres:
        raise ValueError("Catalogue vide")

    catalogue = pd.DataFrame(livres)

    print("Catalogue :", len(catalogue), "livres")
    return catalogue


# 6. Vérifier les livres
def verifier_livres(ventes, catalogue):
    manquants = ventes[
        ~ventes["book_name"].isin(catalogue["title"])
    ]

    print("Ventes sans prix :", len(manquants))

    if len(manquants) > 0:
        raise ValueError("Certains livres n'ont pas de prix")


# 7. Préparer la table books
def preparer_livres(ventes, catalogue):
    livres = ventes[
        ["book_id", "book_name"]
    ].drop_duplicates()

    livres = livres.merge(
        catalogue,
        left_on="book_name",
        right_on="title",
        how="left",
        validate="one_to_one"
    )

    if livres["price_gbp"].isna().any():
        raise ValueError("Prix manquants dans books")

    livres = livres[
        ["book_id", "title", "price_gbp"]
    ]

    print("Livres préparés :", len(livres))
    return livres


# 8. Enrichir les ventes
def enrichir_ventes(ventes, catalogue):
    ventes_enrichies = ventes.merge(
        catalogue,
        left_on="book_name",
        right_on="title",
        how="left",
        validate="many_to_one"
    )

    if ventes_enrichies["price_gbp"].isna().any():
        raise ValueError("Prix manquants dans les ventes")

    print("Ventes enrichies :", len(ventes_enrichies))
    return ventes_enrichies


# 9. Récupérer le taux GBP/EUR
def extraire_taux_change():
    url = "https://api.frankfurter.dev/v1/latest"

    reponse = requests.get(
        url,
        params={"base": "GBP", "symbols": "EUR"},
        timeout=10
    )
    reponse.raise_for_status()

    donnees = reponse.json()
    taux = float(donnees["rates"]["EUR"])

    if taux <= 0:
        raise ValueError("Taux de change invalide")

    print("Date du taux :", donnees["date"])
    print("Taux GBP/EUR :", taux)

    return taux


# 10. Calculer le chiffre d'affaires
def calculer_ca(ventes, taux):
    ventes = ventes.copy()

    ventes["revenue_gbp"] = (
        ventes["quantity"]
        * ventes["price_gbp"]
        * (1 - ventes["discount_rate"])
    )

    ventes["revenue_eur"] = ventes["revenue_gbp"] * taux

    print("Chiffres d'affaires calculés")
    return ventes


# 11. Préparer sales_clean sans données personnelles
def preparer_ventes(ventes):
    colonnes = [
        "order_id",
        "order_date",
        "book_id",
        "country_code",
        "channel_code",
        "quantity",
        "discount_rate",
        "revenue_gbp",
        "revenue_eur"
    ]

    sales_clean = ventes[colonnes].copy()

    print("Ventes nettoyées :", len(sales_clean))
    return sales_clean


# 12. Agréger les ventes par pays
def agreger_ventes(ventes, pays):
    ventes = ventes.merge(
        pays[["country_code", "country_name"]],
        on="country_code",
        how="left",
        validate="many_to_one"
    )

    if ventes["country_name"].isna().any():
        raise ValueError("Pays manquants après jointure")

    resultat = ventes.groupby(
        ["country_code", "country_name"],
        as_index=False
    ).agg(
        total_orders=("order_id", "nunique"),
        total_quantity=("quantity", "sum"),
        total_revenue_gbp=("revenue_gbp", "sum"),
        total_revenue_eur=("revenue_eur", "sum")
    )

    resultat["total_revenue_gbp"] = (
        resultat["total_revenue_gbp"].round(2)
    )

    resultat["total_revenue_eur"] = (
        resultat["total_revenue_eur"].round(2)
    )

    print("Pays avec ventes :", len(resultat))
    return resultat


# 13. Stocker les 4 tables dans SQLite
def stocker_resultats(pays, livres, sales_clean, sales_by_country):

    with sqlite3.connect("bookworld_final.db") as connexion:
        connexion.execute("PRAGMA foreign_keys = ON")

        pays_final = pays[
            ["country_code", "country_name"]
        ].drop_duplicates()

        # Vider les tables dans l'ordre des dépendances
        for table in [
            "sales_clean",
            "sales_by_country",
            "books",
            "countries"
        ]:
            connexion.execute(f"DELETE FROM {table}")

        # Insérer les pays
        pays_final.to_sql(
            "countries",
            connexion,
            if_exists="append",
            index=False
        )

        # Insérer les livres
        livres.to_sql(
            "books",
            connexion,
            if_exists="append",
            index=False
        )

        # Insérer les ventes nettoyées
        sales_clean.to_sql(
            "sales_clean",
            connexion,
            if_exists="append",
            index=False
        )

        # Insérer les agrégations
        sales_by_country.to_sql(
            "sales_by_country",
            connexion,
            if_exists="append",
            index=False
        )

        # Vérifier les clés étrangères
        erreurs = connexion.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

        if erreurs:
            raise ValueError(
                f"Clés étrangères invalides : {erreurs}"
            )

    print("Les 4 tables ont été mises à jour avec succès !")


# 14. Fonction principale
def main():
    try:
        # Extraction CSV
        ventes = extraire_ventes()

        # Contrôle qualité
        verifier_qualite(ventes)

        # Extraction SQLite
        pays, canaux, categories = extraire_referentiels()
        verifier_pays(ventes, pays)

        # Scraping
        catalogue = extraire_catalogue()
        verifier_livres(ventes, catalogue)

        # Préparer les livres
        livres = preparer_livres(ventes, catalogue)

        # Enrichissement
        ventes_enrichies = enrichir_ventes(ventes, catalogue)

        # Taux de change
        taux = extraire_taux_change()

        # Calcul des chiffres d'affaires
        ventes_enrichies = calculer_ca(ventes_enrichies, taux)

        # Préparer les ventes nettoyées
        sales_clean = preparer_ventes(ventes_enrichies)

        # Agréger les ventes par pays
        sales_by_country = agreger_ventes(ventes_enrichies, pays)

        # Enregistrer les 4 tables
        stocker_resultats(
            pays,
            livres,
            sales_clean,
            sales_by_country
        )

        print("\nPipeline terminé avec succès !")

    except Exception as erreur:
        print("Erreur pendant le pipeline :", erreur)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
