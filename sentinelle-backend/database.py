import geopandas as gpd
import os

def charger_donnees():
    # Définition du chemin vers le dossier data
    base_path = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_path, "data")
    
    # NOMS DE FICHIERS CONFIRMÉS PAR LE FIND
    file_ecoles = os.path.join(data_dir, "export.geojson")
    file_zones = os.path.join(data_dir, "lcz_bordeaux.geojson")
    
    print(f"🔍 Tentative de lecture : {file_ecoles}")
    
    # Vérification de présence physique
    if not os.path.exists(file_ecoles):
        print(f"❌ ERREUR : {file_ecoles} introuvable !")
        return None, None
    
    try:
        # Chargement des GeoJSON
        ecoles = gpd.read_file(file_ecoles)
        zones = gpd.read_file(file_zones)
        print("✅ GÉO-DONNÉES : Chargement réussi !")
        return ecoles, zones
    except Exception as e:
        print(f"❌ ERREUR LECTURE : {e}")
        return None, None
