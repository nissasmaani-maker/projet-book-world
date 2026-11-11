
import pandas as pd
import sqlite3
import requests
from bs4 import BeautifulSoup


# 1. Extraire les ventes du CSV
def extraire_ventes():
    ventes = pd.read_csv("sales_raw.csv", sep=";")

    print("Ventes :", len(ventes), "lignes")
    return ventes


# 2. Extraire les référentiels SQLite
def extraire_referentiels():
    connexion = sqlite3.connect("bookworld_reference.db")

    try:
        # Requête SQL avec filtre
        pays = pd.read_sql(
        "SELECT * FROM countries",
        connexion
        )

        # Requête SQL avec filtre
        canaux = pd.read_sql(
            "SELECT * FROM channels WHERE is_active = 1",
            connexion
        )

        # Requête pour les règles métier
        categories = pd.read_sql(
            "SELECT * FROM category_rules",
            connexion
        )

    finally:
        connexion.close()

    # Ajouter le pays manquant dans le référentiel
    if "NL" not in pays["country_code"].values:
        nouveau_pays = pd.DataFrame([{
            "country_code": "NL",
            "country_name": "Netherlands"
        }])

        pays = pd.concat([pays, nouveau_pays], ignore_index=True)

    print("Pays :", len(pays), "lignes")
    print("Canaux :", len(canaux), "lignes")
    print("Catégories :", len(categories), "lignes")

    return pays, canaux, categories


# 3. Scraper la première page du catalogue
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
        raise ValueError("Aucun livre trouvé sur le site")

    catalogue = pd.DataFrame(livres)

    print("Catalogue :", len(catalogue), "livres")
    print(catalogue.head())

    return catalogue


# 4. Récupérer le taux de change GBP vers EUR
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
    print("Taux GBP vers EUR :", taux)

    return taux


# 5. Vérifier les pays des ventes
def verifier_pays(ventes, pays):

    pays_manquants = ventes[
        ~ventes["country_code"].isin(pays["country_code"])
    ]

    print("Ventes sans pays dans le référentiel :", len(pays_manquants))
    print(pays_manquants["country_code"].value_counts())


# 6. Vérifier les livres sans prix
def verifier_livres(ventes, catalogue):
    livres_manquants = ventes[
        ~ventes["book_name"].isin(catalogue["title"])
    ]

    print("Ventes sans prix :", len(livres_manquants))
    print(livres_manquants["book_name"].unique())


# 7. Enrichir les ventes avec les prix
def enrichir_ventes(ventes, catalogue):

    ventes_enrichies = ventes.merge(
        catalogue,
        left_on="book_name",
        right_on="title",
        how="left"
    )

    print("Ventes enrichies :", len(ventes_enrichies))
    print(ventes_enrichies[["book_name", "quantity", "price_gbp"]].head())

    return ventes_enrichies


# 8. Calculer le chiffre d'affaires
def calculer_ca(ventes, taux):

    ventes["revenue_gbp"] = (
        ventes["quantity"]
        * ventes["price_gbp"]
        * (1 - ventes["discount_rate"])
    )

    ventes["revenue_eur"] = ventes["revenue_gbp"] * taux

    print(ventes[[
        "quantity",
        "price_gbp",
        "discount_rate",
        "revenue_gbp",
        "revenue_eur"
    ]].head())

    return ventes


# Agréger les ventes par pays
def agreger_ventes(ventes, pays):

    # Ajouter le nom du pays aux ventes
    ventes = ventes.merge(
        pays[["country_code", "country_name"]],
        on="country_code",
        how="left",
        validate="many_to_one"
    )

    # 9. Vérifier qu'aucun nom de pays ne manque
    if ventes["country_name"].isna().any():
        raise ValueError("Certaines ventes n'ont pas de pays associé")

    # Calculer les indicateurs par pays
    sales_by_country = ventes.groupby(
        ["country_code", "country_name"],
        as_index=False
    ).agg(
        total_orders=("order_id", "nunique"),
        total_quantity=("quantity", "sum"),
        total_revenue_gbp=("revenue_gbp", "sum"),
        total_revenue_eur=("revenue_eur", "sum")
    )

    # Arrondir les montants à deux décimales
    sales_by_country["total_revenue_gbp"] = (
        sales_by_country["total_revenue_gbp"].round(2)
    )

    sales_by_country["total_revenue_eur"] = (
        sales_by_country["total_revenue_eur"].round(2)
    )

    print("\nVentes par pays :")
    print(sales_by_country.to_string(index=False))

    return sales_by_country


# Vérifier la qualité des ventes
def verifier_qualite(ventes):
    print("\nContrôle qualité :")
    print("Doublons exacts :", ventes.duplicated().sum())
    print("Valeurs manquantes :")
    print(ventes.isnull().sum())


###. Fonction principale
def main():
    try:
        ventes = extraire_ventes()
        verifier_qualite(ventes)
        pays, canaux, categories = extraire_referentiels()
        # Vérifier les pays des ventes
        verifier_pays(ventes, pays)

        catalogue = extraire_catalogue()

        # Vérifier les livres
        verifier_livres(ventes, catalogue)
        ventes_enrichies = enrichir_ventes(ventes, catalogue)
        taux = extraire_taux_change()

        ventes_enrichies = calculer_ca(ventes_enrichies, taux)

        sales_by_country = agreger_ventes(ventes_enrichies, pays)

        print("Toutes les extractions ont réussi !")

    except Exception as erreur:
        print("Erreur pendant l'extraction :", erreur)
        raise SystemExit(1)


# Point d'entrée du programme
if __name__ == "__main__":
    main()

