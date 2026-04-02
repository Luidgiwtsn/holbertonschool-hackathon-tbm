import geopandas as gpd
import os

def charger_donnees():
    """
    Charge les fichiers GeoJSON et harmonise les systèmes de coordonnées (CRS).
    Indispensable pour que les calculs de 'contains' ou 'intersects' fonctionnent.
    """
    # 1. Définition des chemins
    base_path = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_path, "data")
    
    file_ecoles = os.path.join(data_dir, "export.geojson")
    file_zones = os.path.join(data_dir, "lcz_bordeaux.geojson")
    
    print(f"🔍 Initialisation de la base de données...")

    # 2. Vérification de la présence des fichiers
    if not os.path.exists(file_ecoles):
        print(f"❌ ERREUR CRITIQUE : {file_ecoles} introuvable !")
        return None, None
    if not os.path.exists(file_zones):
        print(f"⚠️ ALERTE : {file_zones} introuvable ! Analyse spatiale limitée.")
        # On peut continuer avec ecoles seulement si besoin, mais ici on gère l'erreur
        return None, None

    try:
        # 3. Lecture des GeoJSON
        ecoles = gpd.read_file(file_ecoles)
        zones = gpd.read_file(file_zones)

        # 4. HARMONISATION DU SYSTÈME DE COORDONNÉES (CRS)
        # On force tout en EPSG:4326 (Coordonnées GPS standards WGS84)
        # C'est l'étape qui évite les erreurs de calcul spatial
        if ecoles.crs != "EPSG:4326":
            print(f"🔄 Reprojection des écoles vers EPSG:4326...")
            ecoles = ecoles.to_crs(epsg=4326)
            
        if zones.crs != "EPSG:4326":
            print(f"🔄 Reprojection des zones LCZ vers EPSG:4326...")
            zones = zones.to_crs(epsg=4326)

        # 5. NETTOYAGE DES COLONNES
        # On passe les colonnes en MAJUSCULES pour correspondre à ton analysis.py (VER, BUR, VHR)
        zones.columns = [c.upper() if c != 'geometry' else 'geometry' for c in zones.columns]

        print("✅ GÉO-DONNÉES : Chargement et synchronisation réussis !")
        return ecoles, zones

    except Exception as e:
        print(f"❌ ERREUR LECTURE OU TRAITEMENT : {e}")
        return None, None
