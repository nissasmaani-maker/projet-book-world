from flask import Flask, jsonify, request
import sqlite3
from functools import wraps
import secrets
import os

app = Flask(__name__)



from dotenv import load_dotenv
load_dotenv()
VALID_KEYS = {k.strip() for k in os.environ['API_KEY'].split(',') if k.strip()}

def require_api_key(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        key = request.headers.get("X-API-Key", "")
        if not key or not any(secrets.compare_digest(key, k) for k in VALID_KEYS):
            return jsonify(error="Clé API invalide ou absente"), 401
        return f(*args, **kwargs)
    return wrapper



# Récupérer les ventes par pays
@app.route("/sales_by_country", methods=["GET"])
@require_api_key
def sales_by_country():
    connexion = sqlite3.connect("bookworld_final.db")
    connexion.row_factory = sqlite3.Row

    ventes = connexion.execute(
        "SELECT * FROM sales_by_country"
    ).fetchall()

    connexion.close()

    return jsonify([dict(vente) for vente in ventes])




# Récupérer les ventes d'un pays précis
@app.route("/sales_by_country/<country_code>", methods=["GET"])
@require_api_key
def ventes_par_pays(country_code):

    connexion = sqlite3.connect("bookworld_final.db")
    connexion.row_factory = sqlite3.Row

    vente = connexion.execute(
        "SELECT * FROM sales_by_country WHERE country_code = ?",
        (country_code.upper(),)
    ).fetchone()

    connexion.close()

    if vente is None:
        return jsonify({"error": "Pays introuvable"}), 404

    return jsonify(dict(vente))




# Récupérer les indicateurs globaux
@app.route("/kpis", methods=["GET"])
@require_api_key
def kpis():
    connexion = sqlite3.connect("bookworld_final.db")
    connexion.row_factory = sqlite3.Row

    resultat = connexion.execute("""
        SELECT
            SUM(total_orders) AS total_orders,
            SUM(total_quantity) AS total_quantity,
            ROUND(SUM(total_revenue_gbp), 2) AS total_revenue_gbp,
            ROUND(SUM(total_revenue_eur), 2) AS total_revenue_eur
        FROM sales_by_country
    """).fetchone()

    connexion.close()

    return jsonify(dict(resultat))



# Classement des pays par chiffre d'affaires
@app.route("/top_countries", methods=["GET"])
@require_api_key
def top_countries():

    connexion = sqlite3.connect("bookworld_final.db")
    connexion.row_factory = sqlite3.Row

    resultats = connexion.execute("""
        SELECT *
        FROM sales_by_country
        ORDER BY total_revenue_eur DESC
    """).fetchall()

    connexion.close()

    return jsonify([dict(pays) for pays in resultats])


if __name__ == "__main__":
    app.run(debug=False)
