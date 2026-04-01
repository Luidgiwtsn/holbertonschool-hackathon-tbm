from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from unidecode import unidecode
from database import charger_donnees
from analysis import calcul_score, get_barometre, get_recommandation
from models import Diagnostic
import geopandas as gpd
import os
from enum import Enum
import uvicorn

class ProfilUtilisateur(str, Enum):
    public = "public"
    pro = "pro"

app = FastAPI(title="Sentinelle API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ecoles = None
zones = None
argile = None

# --- INIT ---
def initialiser_systeme():
    global ecoles, zones, argile

    ecoles, zones = charger_donnees()

    if ecoles is None or zones is None:
        print("❌ Problème chargement données")

    # nettoyage
    if ecoles is not None:
        ecoles = ecoles[ecoles.geometry.notnull()]
        ecoles = ecoles[~ecoles.geometry.is_empty]

        col_nom = "name" if "name" in ecoles.columns else ecoles.columns[0]
        ecoles["nom_normalise"] = ecoles[col_nom].apply(
            lambda x: unidecode(str(x)).lower().strip()
        )

    print("🚀 Backend prêt")

initialiser_systeme()

@app.get("/")
def root():
    return {"status": "API OK"}

@app.get("/diagnostic/recherche/{ecole_name}", response_model=Diagnostic)
def diagnostic(ecole_name: str, categorie: ProfilUtilisateur = Query(...)):

    nom = unidecode(ecole_name).lower().strip()
    print("🔍 Recherche :", nom)

    match = ecoles[ecoles["nom_normalise"].str.contains(nom)]

    if match.empty:
        raise HTTPException(404, "École non trouvée")

    ecole = match.iloc[0]

    # 🔥 sécurité geometry
    if ecole.geometry is None or ecole.geometry.is_empty:
        raise HTTPException(500, "Géométrie invalide")

    # 🔥 zones
    try:
        z_match = zones[zones.geometry.contains(ecole.geometry)]

        if not z_match.empty:
            ver = float(z_match.iloc[0].get("VER", 0))
            bur = float(z_match.iloc[0].get("BUR", 100))
            vhr = float(z_match.iloc[0].get("VHR", 0))
        else:
            ver, bur, vhr = 0.0, 100.0, 0.0

    except:
        ver, bur, vhr = 0.0, 100.0, 0.0

    score = calcul_score(ver, bur, vhr)
    barometre = get_barometre(score)

    reco = get_recommandation(score, ver, bur, vhr)

    return Diagnostic(
        nom=str(ecole.get("name")),
        score_alerte=score,
        barometre=barometre,
        recommandation=reco,
        alea_argile="Non testé"
    )

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
