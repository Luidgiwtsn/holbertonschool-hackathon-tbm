import geopandas as gpd
import os

def charger_donnees():
    base_path = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_path, "data")

    file_ecoles = os.path.join(data_dir, "export.geojson")
    file_zones = os.path.join(data_dir, "lcz_bordeaux.geojson")

    print(f"📂 écoles : {file_ecoles}")
    print(f"📂 zones : {file_zones}")

    if not os.path.exists(file_ecoles):
        print("❌ export.geojson introuvable")
        return None, None

    if not os.path.exists(file_zones):
        print("❌ lcz_bordeaux.geojson introuvable")
        return None, None

    try:
        ecoles = gpd.read_file(file_ecoles)
        zones = gpd.read_file(file_zones)

        ecoles = ecoles.to_crs(epsg=4326)
        zones = zones.to_crs(epsg=4326)

        print("✅ données chargées")

        return ecoles, zones

    except Exception as e:
        print(f"❌ erreur lecture : {e}")
        return None, None
