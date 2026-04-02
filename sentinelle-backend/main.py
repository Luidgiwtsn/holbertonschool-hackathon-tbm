from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from unidecode import unidecode
from pydantic import BaseModel
from typing import Dict, List
import uvicorn
import geopandas as gpd
import pandas as pd
import os
from enum import Enum
from models import DiagnosticResponse

# --- MODÈLES DE DONNÉES ---
class ProfilUtilisateur(str, Enum):
    public = "public"
    pro = "pro"

class DiagnosticResponse(BaseModel):
    nom: str
    score_alerte: float
    barometre: str
    recommandation: Dict[str, List[str]]
    alea_argile: str

app = FastAPI(title="Sentinelle API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variables globales pour stocker les données en mémoire
ecoles, zones, argile = None, None, None

def initialiser_systeme():
    global ecoles, zones, argile
    try:
        from database import charger_donnees
        # On récupère les GeoDataFrames synchronisés par database.py
        ecoles, zones = charger_donnees()
        
        base_dir = os.path.dirname(__file__)
        # Chargement de l'aléa argile (RGA)
        geojson_path = os.path.join(base_dir, 'data', 'ri_alearga_s.geojson')
        if os.path.exists(geojson_path):
            argile = gpd.read_file(geojson_path).to_crs(epsg=4326)
            argile.columns = [c.lower() for c in argile.columns]
        
        if ecoles is not None:
            # Normalisation du nom pour la recherche textuelle
            col_nom = "name" if "name" in ecoles.columns else ecoles.columns[0]
            ecoles["nom_normalise"] = ecoles[col_nom].apply(
                lambda x: unidecode(str(x)).lower().strip()
            )
        
        print("✅ Backend Initialisé : Données prêtes et synchronisées.")
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation : {e}")

# Lancement au démarrage
initialiser_systeme()

def get_alea_argile(point):
    """Recherche spatiale de l'aléa retrait-gonflement des argiles."""
    if argile is None or argile.empty: return "Indisponible"
    # Petit tampon de 50m autour de l'école pour capter l'aléa local
    match = argile[argile.geometry.intersects(point.buffer(0.0005))] 
    if not match.empty:
        # On cherche la colonne de l'aléa (nommée souvent 'alea' ou 'niv_alea')
        for col in ['alea', 'niv_alea', 'classe']:
            if col in match.columns:
                return str(match.iloc[0][col])
    return "Faible"

@app.get("/diagnostic/recherche/{ecole_name}", response_model=DiagnosticResponse)
async def diagnostic(ecole_name: str, categorie: ProfilUtilisateur = Query(ProfilUtilisateur.public)):
    # Import local pour éviter les imports circulaires
    from analysis import calcul_score, get_barometre, get_recommandation
    
    nom_cherche = unidecode(ecole_name).lower().strip()
    match = ecoles[ecoles["nom_normalise"].str.contains(nom_cherche)]
    
    if match.empty:
        raise HTTPException(404, "École non trouvée")
    
    row = match.iloc[0]
    
    # --- LOGIQUE SPATIALE LCZ (Chaleur) ---
    # On cherche dans quelle zone LCZ se trouve le point de l'école
    z = zones[zones.geometry.contains(row.geometry)]
    
    if not z.empty:
        # On récupère les indicateurs VER, BUR, VHR (formatés par database.py)
        v = float(z.iloc[0].get("VER", 0))
        b = float(z.iloc[0].get("BUR", 0))
        vh = float(z.iloc[0].get("VHR", 0))
    else:
        # Valeurs par défaut si hors zone (pour éviter le 100% rouge)
        v, b, vh = 20, 50, 30

    # Calcul via le moteur analysis.py
    score = calcul_score(v, b, vh)
    recos = get_recommandation(score, v, b, vh)
    
    # Filtrage des recommandations selon le profil (Diagnostic 7x4)
    reco_f = {}
    if categorie == ProfilUtilisateur.pro:
        reco_f["🏗️ Infrastructure"] = recos.get("decideurs", [])
        reco_f["🏫 Gestion École"] = recos.get("ecole", [])
    else:
        reco_f["🧒 Santé & Familles"] = recos.get("familles", [])
        reco_f["📢 Engagement Citoyen"] = recos.get("citoyens", [])

    return DiagnosticResponse(
        nom=str(row.get("name", "École")),
        score_alerte=round(score, 2),
        barometre=get_barometre(score),
        recommandation=reco_f,
        alea_argile=get_alea_argile(row.geometry)
    )

@app.get("/diagnostic/simulation/{ecole_name}")
async def simulation(ecole_name: str):
    nom_cherche = unidecode(ecole_name).lower().strip()
    match = ecoles[ecoles["nom_normalise"].str.contains(nom_cherche)]
    if match.empty: raise HTTPException(404)
    
    alea = get_alea_argile(match.iloc[0].geometry).lower()
    
    # Simulation simplifiée de ROI (Retour sur Investissement)
    s_traitee = 450.0 # m² de cour
    cout = s_traitee * 150 # 150€/m² pour désimperméabiliser
    # Si aléa fort, on simule une économie sur les futures fissures
    gain = 65000.0 if any(x in alea for x in ["fort", "moyen", "3", "2"]) else 15000.0
    
    return {
        "surface": f"{s_traitee} m²",
        "investissement": f"{cout:,} €".replace(",", " "),
        "economie": f"{gain:,} €".replace(",", " "),
        "bilan": "PROJET RENTABLE (Prévention RGA)" if gain > cout else "INVESTISSEMENT SANTÉ PUBLIQUE"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
