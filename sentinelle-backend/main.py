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
class ProfilUtilisateur(str, Enum):
    public = "public"
    pro = "pro"


# --- INIT API ---
app = FastAPI()


# --- CORS ---
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

    ecoles = ecoles.to_crs(epsg=4326)
    zones = zones.to_crs(epsg=4326)

    if argile is not None:
        argile = argile.to_crs(epsg=4326)

    ecoles["nom_normalise"] = ecoles["name"].apply(
        lambda x: unidecode(str(x)).lower().strip()
    )

    print("🚀 Backend OK")


initialiser_systeme()


# --- SCORE CHALEUR ---
def score_chaleur(delta):
    try:
        delta = float(delta)
    except:
        return 40

    if delta >= 4:
        return 100
    elif delta >= 3:
        return 85
    elif delta >= 2:
        return 70
    elif delta >= 1:
        return 50
    else:
        return 30


# --- SCORE ARGILE ---
def score_argile(niveau):
    niveau = str(niveau).lower()

    if "fort" in niveau:
        return 20
    elif "moyen" in niveau:
        return 10
    else:
        return 0


# --- DIAGNOSTIC ---
@app.get("/diagnostic/recherche/{ecole_name}", response_model=Diagnostic)
def diagnostic(ecole_name: str, categorie: ProfilUtilisateur = Query(...)):

    nom = unidecode(ecole_name).lower().strip()

    match = ecoles[ecoles["nom_normalise"].str.contains(nom, na=False)]

    if match.empty:
        raise HTTPException(404, "École non trouvée")

    ecole = match.iloc[0]

    # --- CHALEUR ---
    try:
        zone_match = zones[zones.geometry.intersects(ecole.geometry)]

        if not zone_match.empty:
            row = zone_match.iloc[0]
        else:
            ecole_gdf = gpd.GeoDataFrame([ecole], geometry=[ecole.geometry], crs=ecoles.crs)
            joined = gpd.sjoin_nearest(ecole_gdf, zones, how="left")
            row = joined.iloc[0]

        delta = (
            row.get("delta") or
            row.get("temperature") or
            row.get("value") or
            row.get("gridcode") or
            0
        )

        score_temp = score_chaleur(delta)
        niveau_chaleur = f"+{delta}°C"

    except:
        score_temp = 40
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
    except:
        niveau_argile = "faible"

    # --- SCORE FINAL ---
    score = int(score_temp * 0.8 + score_argile(niveau_argile) * 0.2)
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

    lat = ecole.geometry.y
    lon = ecole.geometry.x

    nom_affiche = f"{ecole.get('name')} ({round(lat,4)}, {round(lon,4)})"

    return Diagnostic(
        nom=nom_affiche,
        score_alerte=score,
        barometre=barometre,
        recommandation=reco_final,
        alea_argile=f"{niveau_chaleur} | Argile: {niveau_argile}"
    )


# --- SIMULATION AMÉLIORÉE ---
@app.get("/diagnostic/simulation/{ecole_name}")
def simulation(ecole_name: str):

    nom = unidecode(ecole_name).lower().strip()

    match = ecoles[ecoles["nom_normalise"].str.contains(nom, na=False)]

    if match.empty:
        raise HTTPException(404, "École non trouvée")

    ecole = match.iloc[0]

    # --- CHALEUR ---
    try:
        zone_match = zones[zones.geometry.intersects(ecole.geometry)]

        if not zone_match.empty:
            row = zone_match.iloc[0]
        else:
            ecole_gdf = gpd.GeoDataFrame([ecole], geometry=[ecole.geometry], crs=ecoles.crs)
            row = gpd.sjoin_nearest(ecole_gdf, zones).iloc[0]

        delta = float(
            row.get("delta") or
            row.get("temperature") or
            row.get("value") or
            row.get("gridcode") or
            1
        )
    except:
        delta = 1

    # --- ARGILE ---
    try:
        if argile is not None:
            argile_match = argile[argile.geometry.intersects(ecole.geometry)]
            if not argile_match.empty:
                niveau_argile = str(argile_match.iloc[0].get("niv_alea", "faible")).lower()
            else:
                niveau_argile = "faible"
        else:
            niveau_argile = "faible"
    except:
        niveau_argile = "faible"

    # --- TYPE ECOLE ---
    type_ecole = str(ecole.get("school:FR", "")).lower()

    if "lycee" in type_ecole:
        surface_base = 2500
    elif "college" in type_ecole:
        surface_base = 1800
    elif "maternelle" in type_ecole:
        surface_base = 700
    else:
        surface_base = 1200

    # --- CALCULS ---
    surface = surface_base * (delta / 4)
    cout = surface * 120

    gain = surface * 50

    if "fort" in niveau_argile:
        gain *= 2
    elif "moyen" in niveau_argile:
        gain *= 1.5

    if delta > 3:
        gain *= 1.3

    bilan = gain - cout

    profil = "STRUCTUREL (Argile)" if "fort" in niveau_argile else "THERMIQUE (Chaleur)"

    return {
        "profil_risque": profil,
        "simulation": {
            "surface_renaturee": f"{round(surface)} m²",
            "investissement_estime": f"{round(cout)} €",
            "economie_reparation_evitee": f"{round(gain)} €",
            "bilan_net_20_ans": f"{round(bilan)} €"
        },
        "conclusion": "INVESTISSEMENT RENTABLE" if bilan > 0 else "COÛT NÉCESSAIRE"
    }


# --- RUN ---
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)