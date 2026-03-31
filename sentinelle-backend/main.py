# main.py
from fastapi import FastAPI, HTTPException
from database import charger_donnees
from analysis import calcul_score, get_barometre, get_recommandation
from models import Diagnostic

app = FastAPI(title="Sentinelle Écoles API")

# Charger les données au démarrage
ecoles, zones = charger_donnees()

@app.get("/")
def root():
    return {"message": "API Sentinelle Écoles active"}

@app.get("/diagnostic/{ecole_id}", response_model=Diagnostic)
def diagnostic(ecole_id: str):
    # 1️⃣ Trouver l'école
    ecole = ecoles[ecoles["id"] == ecole_id]
    if ecole.empty:
        raise HTTPException(status_code=404, detail="École non trouvée")

    # 2️⃣ Identifier la zone contenant l'école
    zone = zones[zones.geometry.contains(ecole.geometry.values[0])]
    if zone.empty:
        raise HTTPException(status_code=404, detail="Zone non trouvée")
    zone = zone.iloc[0]

    # 3️⃣ Récupérer les données nécessaires
    ver = zone["VER"]
    bur = zone["BUR"]
    vhr = zone["VHR"]

    # 4️⃣ Calculer le score
    score = calcul_score(ver, bur, vhr)

    # 5️⃣ Déterminer baromètre
    barometre = get_barometre(score)

    # 6️⃣ Générer recommandations
    recommandation = get_recommandation(score, ver, bur, vhr)

    # 7️⃣ Retourner la réponse
    return Diagnostic(
        nom=ecole.iloc[0]["name"],
        score_alerte=score,
        barometre=barometre,
        recommandation=recommandation
    )
