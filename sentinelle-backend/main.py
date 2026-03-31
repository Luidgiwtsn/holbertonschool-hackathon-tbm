from fastapi import FastAPI, HTTPException
from unidecode import unidecode
from database import charger_donnees
from analysis import calcul_score, get_barometre, get_recommandation
from models import Diagnostic
import pandas as pd

app = FastAPI(title="Sentinelle Écoles API")

# Charger les données
ecoles, zones = charger_donnees()

# Normalisation des noms pour la recherche
ecoles["nom_normalise"] = ecoles["name"].apply(
    lambda x: unidecode(str(x)).lower().strip() if pd.notnull(x) else ""
)

@app.get("/")
def root():
    return {"message": "API Sentinelle Écoles active"}

@app.get("/diagnostic/ecoles")
def list_ecoles():
    """Retourne la liste de toutes les écoles et leurs adresses, en remplaçant les NaN par des chaînes vides"""
    result = []
    for _, row in ecoles.iterrows():
        name = row["name"] if pd.notnull(row["name"]) else ""
        address = row.get("address") if pd.notnull(row.get("address")) else ""
        result.append({"name": name, "address": address})
    return result

@app.get("/diagnostic/{ecole_name}", response_model=Diagnostic)
def diagnostic(ecole_name: str):
    # Normaliser le nom de l'école reçu dans l'URL
    nom_normalise = unidecode(ecole_name).lower().strip()
    ecole = ecoles[ecoles["nom_normalise"] == nom_normalise]

    if ecole.empty:
        raise HTTPException(status_code=404, detail="École non trouvée")

    # Récupérer la zone correspondante à l'école
    try:
        geometry = ecole.geometry.values[0]
    except (AttributeError, IndexError):
        raise HTTPException(status_code=404, detail="École sans géométrie")

    zone = zones[zones.geometry.contains(geometry)]
    if zone.empty:
        raise HTTPException(status_code=404, detail="Zone non trouvée")
    zone = zone.iloc[0]

    # Récupérer les indicateurs et gérer les NaN
    ver = float(zone.get("VER", 0) or 0)
    bur = float(zone.get("BUR", 0) or 0)
    vhr = float(zone.get("VHR", 0) or 0)

    score = calcul_score(ver, bur, vhr)
    barometre = get_barometre(score)
    recommandation = get_recommandation(score, ver, bur, vhr)

    return Diagnostic(
        nom=ecole.iloc[0]["name"] or "",
        score_alerte=score,
        barometre=barometre,
        recommandation=recommandation
    )
