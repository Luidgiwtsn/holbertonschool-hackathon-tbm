from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from unidecode import unidecode
from database import charger_donnees
from analysis import calcul_score, get_barometre, get_recommandation
from models import Diagnostic
import pandas as pd
import uvicorn
import geopandas as gpd
import os
from enum import Enum

# --- PROFILS ---
class ProfilUtilisateur(str, Enum):
    public = "public"
    pro = "pro"

app = FastAPI()

# ✅ CORS FIX
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

def initialiser_systeme():
    global ecoles, zones, argile
    ecoles, zones = charger_donnees()

    base_dir = os.path.dirname(__file__)
    path_argile = os.path.join(base_dir, "data", "ri_alearga_s.geojson")

    if os.path.exists(path_argile):
        argile = gpd.read_file(path_argile).to_crs(epsg=4326)
        argile.columns = [c.lower() for c in argile.columns]

    ecoles = ecoles.to_crs(epsg=4326)
    zones = zones.to_crs(epsg=4326)

    ecoles["nom_normalise"] = ecoles["name"].apply(
        lambda x: unidecode(str(x)).lower().strip()
    )

    print("🚀 Backend OK")

initialiser_systeme()

# --- ARGILE ---
def get_alea_argile(point):
    if argile is None or argile.empty:
        return "Indisponible"

    gdf = gpd.GeoDataFrame(geometry=[point], crs="EPSG:4326").to_crs(3857)
    buffer = gdf.buffer(50).to_crs(4326).iloc[0]

    match = argile[argile.geometry.intersects(buffer)]

    if not match.empty:
        col = "alea" if "alea" in match.columns else match.columns[0]
        return ", ".join(match[col].astype(str).unique())

    return "Faible/Nul"

# --- DIAGNOSTIC ---
@app.get("/diagnostic/recherche/{ecole_name}", response_model=Diagnostic)
def diagnostic(ecole_name: str, categorie: ProfilUtilisateur = Query(...)):

    nom = unidecode(ecole_name).lower().strip()

    # ✅ FIX crash ici
    match = ecoles[ecoles["nom_normalise"].str.contains(nom, na=False)]

    if match.empty:
        raise HTTPException(404, "École non trouvée")

    ecole = match.iloc[0]

    z = zones[zones.geometry.contains(ecole.geometry)]

    ver = float(z.iloc[0].get("VER", 0)) if not z.empty else 0
    bur = float(z.iloc[0].get("BUR", 100)) if not z.empty else 100
    vhr = float(z.iloc[0].get("VHR", 0)) if not z.empty else 0

    score = calcul_score(ver, bur, vhr)
    barometre = get_barometre(score)
    alea = get_alea_argile(ecole.geometry)

    reco = get_recommandation(score, ver, bur, vhr)

    reco_final = {}

    if categorie == ProfilUtilisateur.pro:
        reco_final["🏗️ infrastructure"] = reco["decideurs"]
        reco_final["🏫 ecole"] = reco["ecole"]
    else:
        reco_final["👨‍👩‍👧 familles"] = reco["familles"]
        reco_final["📢 citoyens"] = reco["citoyens"]

    return Diagnostic(
        nom=str(ecole.get("name")),
        score_alerte=round(score, 2),
        barometre=barometre,
        recommandation=reco_final,
        alea_argile=alea
    )

# --- SIMULATION ---
@app.get("/diagnostic/simulation/{ecole_name}")
def simulation(ecole_name: str, projet_veg: float = Query(30.0)):

    nom = unidecode(ecole_name).lower().strip()
    match = ecoles[ecoles["nom_normalise"].str.contains(nom, na=False)]

    if match.empty:
        raise HTTPException(404)

    ecole = match.iloc[0]
    alea = get_alea_argile(ecole.geometry).lower()

    surface = 1000 * (projet_veg / 100)
    cout = surface * 150
    gain = surface * 50 if "fort" in alea else 0

    return {
        "ecole": ecole.get("name"),
        "profil_risque": "STRUCTUREL" if gain > 0 else "THERMIQUE",
        "simulation": {
            "surface_renaturee": f"{round(surface,1)} m²",
            "investissement_estime": f"{round(cout,2)} €",
            "economie_reparation_evitee": f"{round(gain,2)} €",
            "bilan_net_20_ans": f"{round(gain - cout,2)} €"
        },
        "conclusion": "RENTABLE" if gain > cout else "COÛT"
    }

# --- RUN ---
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)