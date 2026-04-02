import geopandas as gpd
import os

def charger_donnees():
    base = os.path.dirname(__file__)
    data = os.path.join(base, "data")

    file_ecoles = os.path.join(data, "export.geojson")
    file_zones = os.path.join(data, "Zone-de-Chaleur-et-Fraicheur.geojson")

    print("🔍 chargement :", file_ecoles)

    try:
        ecoles = gpd.read_file(file_ecoles, engine="pyogrio")
        zones = gpd.read_file(file_zones, engine="pyogrio")

        print("✅ données chargées")
        print("COLONNES ZONES :", zones.columns)

        return ecoles, zones

    except Exception as e:
        print("❌ erreur :", e)
        return None, None