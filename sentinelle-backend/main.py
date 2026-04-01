from fastapi import FastAPI, HTTPException
from unidecode import unidecode
from database import charger_donnees
from analysis import calcul_score, get_barometre, get_recommandation
from models import Diagnostic
import pandas as pd
import uvicorn
import geopandas as gpd
import os

# Initialisation de l'API FastAPI
app = FastAPI(title="Sentinelle Écoles API", version="1.3.2")

# --- VARIABLES GLOBALES (Stockage des données en mémoire vive) ---
ecoles = None  # Points GPS des établissements
zones = None   # Zones climatiques (LCZ)
argile = None  # Zones d'aléa retrait-gonflement des argiles (BRGM)

def initialiser_systeme():
    """
    Charge et prépare toutes les données géospatiales au démarrage du serveur.
    Cette fonction centralise le "Data Cleaning" pour optimiser les performances.
    """
    global ecoles, zones, argile
    try:
        # 1. Chargement des données métier (via le module database.py)
        ecoles, zones = charger_donnees()
        
        # 2. Chargement de la couche Argile (Source: Géorisques / BRGM)
        base_dir = os.path.dirname(__file__)
        geojson_path = os.path.join(base_dir, 'data', 'ri_alearga_s.geojson')
        
        if os.path.exists(geojson_path):
            # On force le système de coordonnées en WGS84 (Standard GPS)
            argile = gpd.read_file(geojson_path).to_crs(epsg=4326)
            # Normalisation des noms de colonnes en minuscules
            argile.columns = [c.lower() for c in argile.columns]
            print(f"✅ GÉO-DONNÉES ARGILE : Chargées ({len(argile)} zones)")
        
        # 3. Préparation et NETTOYAGE profond de la base écoles
        if ecoles is not None:
            # Conversion en GeoDataFrame si nécessaire
            if not isinstance(ecoles, gpd.GeoDataFrame):
                ecoles = gpd.GeoDataFrame(ecoles, geometry=gpd.points_from_xy(ecoles.lon, ecoles.lat))
            
            ecoles = ecoles.to_crs(epsg=4326)

            # --- GESTION DU "NAN" (DATA CLEANING) ---
            # On remplace les types vides par "Établissement" pour éviter les bugs d'affichage JSON
            colonnes_type = ['school:FR', 'amenity', 'description']
            for col in colonnes_type:
                if col in ecoles.columns:
                    ecoles[col] = ecoles[col].astype(str).replace(['nan', 'None', 'NaN'], 'Établissement')

            # Création d'une colonne de recherche simplifiée (sans accents, minuscules)
            col_nom = "name" if "name" in ecoles.columns else ecoles.columns[0]
            ecoles["nom_normalise"] = ecoles[col_nom].apply(
                lambda x: unidecode(str(x)).lower().strip() if pd.notnull(x) else ""
            )
        print("🚀 Backend Sentinelle opérationnel (Full Data Cleaning).")
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation : {e}")

# Lancement du chargement au démarrage du script
initialiser_systeme()

# --- LOGIQUE GÉOSPATIALE ---

def get_alea_argile(point_ecole):
    """
    Analyse spatiale : vérifie si l'école est sur un sol argileux.
    Utilise un BUFFER de 50 mètres pour compenser l'imprécision du GPS.
    """
    if argile is None or argile.empty: return "Indisponible"
    
    # Passage en projection métrique (EPSG:3857) pour calculer le rayon de 50m
    gdf_ecole = gpd.GeoDataFrame(geometry=[point_ecole], crs="EPSG:4326").to_crs(epsg=3857)
    buffer_50m = gdf_ecole.buffer(50).to_crs(epsg=4326).iloc[0]
    
    # Intersection spatiale entre le cercle de 50m et les polygones d'aléa
    match = argile[argile.geometry.intersects(buffer_50m)]
    
    if not match.empty:
        col_alea = 'alea' if 'alea' in match.columns else match.columns[0]
        res = match[col_alea].astype(str).unique()
        return ", ".join(res)
    
    return "Faible/Nul"

# --- ENDPOINTS API ---

@app.get("/diagnostic/recherche/{ecole_name}", response_model=Diagnostic)
def diagnostic(ecole_name: str):
    """
    Effectue un diagnostic complet de résilience pour une école donnée.
    Couple les données LCZ (climat) et RGA (géologie).
    """
    # Recherche flexible dans la base
    nom_cherche = unidecode(ecole_name).lower().strip()
    match = ecoles[ecoles["nom_normalise"].str.contains(nom_cherche)]
    if match.empty: 
        raise HTTPException(status_code=404, detail="Ecole non trouvée dans la base")

    ecole_row = match.iloc[0]
    
    # Détection de la zone climatique entourant l'école
    z_match = zones[zones.geometry.contains(ecole_row.geometry)]
    
    # Extraction des indices de végétation et bâti
    ver = float(z_match.iloc[0].get("VER", 0)) if not z_match.empty else 0.0
    bur = float(z_match.iloc[0].get("BUR", 100)) if not z_match.empty else 100.0
    vhr = float(z_match.iloc[0].get("VHR", 0)) if not z_match.empty else 0.0

    # Diagnostic argile
    alea_rga = get_alea_argile(ecole_row.geometry)
    
    # Calcul métier (via module analysis.py)
    score = calcul_score(ver, bur, vhr)
    reco = get_recommandation(score, ver, bur, vhr)
    
    # Ajout d'une alerte spécifique si le sol est instable
    if any(x in alea_rga.lower() for x in ["fort", "moyen", "2", "3", "high"]):
        reco += f"\n\n🚨 ALERTE STRUCTURE : Risque RGA détecté ({alea_rga})."

    return Diagnostic(
        nom=str(ecole_row.get("name")),
        score_alerte=round(score, 2),
        barometre=get_barometre(score),
        recommandation=reco,
        alea_argile=alea_rga
    )

@app.get("/diagnostic/simulation/{ecole_name}")
def simulation(ecole_name: str, projet_veg: float = 30.0):
    """
    Simulateur financier : calcule le coût des travaux vs les économies de maintenance.
    Argumentaire : Démontrer que la végétalisation protège le patrimoine bâti.
    """
    nom_cherche = unidecode(ecole_name).lower().strip()
    match = ecoles[ecoles["nom_normalise"].str.contains(nom_cherche)]
    if match.empty: raise HTTPException(status_code=404)
    
    ecole_info = match.iloc[0]
    alea = get_alea_argile(ecole_info.geometry).lower()
    type_ecole = str(ecole_info.get('school:FR', ecole_info.get('amenity', 'Établissement'))).lower()
    
    # 1. Estimation de la surface selon le type (Lycée vs Maternelle)
    surfaces = {"lycee": 2500, "college": 1800, "maternelle": 700, "kindergarten": 400}
    surface_ref = 1000 
    for k, v in surfaces.items():
        if k in type_ecole:
            surface_ref = v
            break

    # 2. Calcul des coûts : 150€/m² pour débitumage + plantation
    surface_a_traiter = (surface_ref * 1.2) * (projet_veg/100)
    cout = surface_a_traiter * 150 
    
    # 3. Calcul du gain : Évitement des fissures (50€/m² de bâtiment sauvé)
    gain = (surface_ref * 50) if any(x in alea for x in ["fort", "3", "moyen", "2"]) else 0
    bilan = gain - cout

    # 4. Retour structuré pour le Front-end
    return {
        "ecole": ecole_info.get("name"),
        "metadata": {
            "type": type_ecole.upper(),
            "alea_sol": alea.upper(),
            "surface_cour_estimee": f"{round(surface_ref * 1.2, 1)} m²"
        },
        "simulation_financiere": {
            "investissement_travaux": f"{round(cout, 2)} €",
            "economie_reparation_evitee": f"{round(gain, 2)} €",
            "bilan_net": f"{round(bilan, 2)} €"
        },
        "analyse_decisionnelle": {
            "priorite": "URGENTE" if bilan > 0 or projet_veg > 50 else "MODÉRÉE",
            "argument": "Rentabilité structurelle confirmée." if bilan > 0 else "Bénéfice majeur : Santé publique et fraîcheur urbaine."
        }
    }

# Lancement du serveur local
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
