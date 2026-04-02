from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from unidecode import unidecode
from database import charger_donnees
from analysis import get_barometre, get_recommandation
from models import Diagnostic

import geopandas as gpd
import os
from enum import Enum
import uvicorn

# --- PROFILS ---
# Types d'utilisateurs
class ProfilUtilisateur(str, Enum):
    public = "public"
    pro = "pro"

# --- INIT API ---
app = FastAPI()

# --- CORS ---
# Autorise le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DATA ---
ecoles = None
zones = None
argile = None

# --- INITIALISATION ---
# Charge les GeoJSON
def initialiser_systeme():
    global ecoles, zones, argile

    ecoles, zones = charger_donnees()

    base = os.path.dirname(__file__)
    path_argile = os.path.join(base, "data", "Zone-Argileuse.geojson")

    if os.path.exists(path_argile):
        argile = gpd.read_file(path_argile, engine="pyogrio")

    if ecoles is None or zones is None:
        print("❌ données non chargées")
        return

    # Projection GPS
    ecoles = ecoles.to_crs(epsg=4326)
    zones = zones.to_crs(epsg=4326)

    if argile is not None:
        argile = argile.to_crs(epsg=4326)

    # Normalisation noms
    ecoles["nom_normalise"] = ecoles["name"].apply(
        lambda x: unidecode(str(x)).lower().strip()
    )

    print("🚀 Backend OK")
    print("📊 colonnes zones:", zones.columns)

initialiser_systeme()

# --- SCORE DELTA ---
# Convertit delta température en score
def score_chaleur(delta):
    try:
        delta = float(delta)
    except:
        return 30

    if delta > 4:
        return 95
    elif delta > 3:
        return 80
    elif delta > 2:
        return 60
    elif delta > 1:
        return 40
    else:
        return 20

# --- SCORE ARGILE ---
# Impact du sol
def score_argile(niveau):
    niveau = str(niveau).lower()

    if "fort" in niveau:
        return 25
    elif "moyen" in niveau:
        return 15
    else:
        return 0

# --- DIAGNOSTIC ---
# Analyse complète
@app.get("/diagnostic/recherche/{ecole_name}", response_model=Diagnostic)
def diagnostic(ecole_name: str, categorie: ProfilUtilisateur = Query(...)):

    nom = unidecode(ecole_name).lower().strip()

    match = ecoles[ecoles["nom_normalise"].str.contains(nom, na=False)]

    if match.empty:
        raise HTTPException(404, "École non trouvée")

    ecole = match.iloc[0]

    # --- CHALEUR (DELTA) ---
    try:
        zone_match = zones[zones.geometry.intersects(ecole.geometry)]

        if not zone_match.empty:
            row = zone_match.iloc[0]
        else:
            # fallback nearest
            ecole_gdf = gpd.GeoDataFrame([ecole], geometry=[ecole.geometry], crs=ecoles.crs)
            joined = gpd.sjoin_nearest(ecole_gdf, zones, how="left")
            row = joined.iloc[0]

        # Lecture dynamique du delta
        delta = (
            row.get("delta") or
            row.get("temperature") or
            row.get("value") or
            row.get("gridcode") or
            0
        )

        print("🌡️ delta:", delta)

        score_temp = score_chaleur(delta)
        niveau_chaleur = f"+{delta}°C"

    except Exception as e:
        print("⚠️ erreur chaleur:", e)
        score_temp = 30
        niveau_chaleur = "inconnu"

    # --- ARGILE ---
    try:
        if argile is not None:
            argile_match = argile[argile.geometry.intersects(ecole.geometry)]

            if not argile_match.empty:
                row = argile_match.iloc[0]
                niveau_argile = row.get("niv_alea") or "faible"
            else:
                niveau_argile = "faible"
        else:
            niveau_argile = "indisponible"

        print("🧱 argile:", niveau_argile)

    except Exception as e:
        print("⚠️ erreur argile:", e)
        niveau_argile = "faible"

    # --- SCORE FINAL ---
    score = score_temp + score_argile(niveau_argile)
    score = min(score, 100)

    barometre = get_barometre(score)

    # --- RECOMMANDATIONS ---
    reco = get_recommandation(score, 0, 0, 0)

    reco_final = {}

    if categorie == ProfilUtilisateur.pro:
        reco_final["🏗️ infrastructure"] = reco["decideurs"]
        reco_final["🏫 ecole"] = reco["ecole"]
    else:
        reco_final["👨‍👩‍👧 familles"] = reco["familles"]
        reco_final["📢 citoyens"] = reco["citoyens"]

    # --- NOM AVEC LOCALISATION ---
    lat = ecole.geometry.y
    lon = ecole.geometry.x

    nom_affiche = f"{ecole.get('name')} ({round(lat,4)}, {round(lon,4)})"

    # --- RÉPONSE ---
    return Diagnostic(
        nom=nom_affiche,
        score_alerte=score,
        barometre=barometre,
        recommandation=reco_final,
        alea_argile=f"{niveau_chaleur} | Argile: {niveau_argile}"
    )

# --- SIMULATION ---
# Simulation simple
@app.get("/diagnostic/simulation/{ecole_name}")
def simulation(ecole_name: str):
    return {
        "simulation": {
            "surface_renaturee": "300 m²",
            "investissement_estime": "45000 €",
            "economie_reparation_evitee": "15000 €",
            "bilan_net_20_ans": "-30000 €"
        },
        "conclusion": "TEST OK"
    }

# --- RUN ---
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)