from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import random
from unidecode import unidecode

from database import charger_donnees
from analysis import (
    calcul_score,
    get_barometre,
    get_recommandation,
    load_argile_data,
    check_risque_argile,
    dimension_to_lcz,
)

app = FastAPI(title="Sentinelle API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ecoles, zones = None, None


@app.on_event("startup")
async def startup():
    global ecoles, zones
    ecoles, zones = charger_donnees()
    load_argile_data()


@app.get("/")
async def root():
    return {"status": "Sentinelle API opérationnelle", "version": "2.0"}


@app.get("/diagnostic/recherche/{ecole_name}")
async def diagnostic(ecole_name: str, categorie: str = "public"):
    if ecoles is None or zones is None:
        raise HTTPException(status_code=500, detail="Base de données non chargée")

    # --- Recherche de l'école ---
    query = unidecode(ecole_name).upper().strip()
    match = ecoles[ecoles["NOM_RECHERCHE"].str.contains(query, na=False)]

    if match.empty:
        raise HTTPException(status_code=404, detail=f"École '{ecole_name}' non trouvée")

    row = match.iloc[0]
    point = row.geometry

    print(f"\n{'='*50}")
    print(f"🔍 ANALYSE : {row['nom']}")

    # --- Recherche de la zone LCZ la plus proche ---
    # Buffer 0.001° ≈ ~100m, suffisant pour couvrir les zones LCZ
    inter = zones[zones.geometry.intersects(point.buffer(0.001))]

    if inter.empty:
        # Fallback : zone la plus proche géométriquement
        print("⚠️  Aucune intersection directe — recherche de la zone la plus proche")
        distances = zones.geometry.distance(point)
        inter = zones.iloc[[distances.idxmin()]]

    # --- Extraction dimension et delta ---
    zone_row = inter.iloc[0]

    # Les colonnes sont en minuscules après database.py
    dimension = zone_row.get("dimension", "BM")
    delta_raw = zone_row.get("delta", 3.0)

    try:
        delta = float(delta_raw) if delta_raw is not None else 3.0
    except (ValueError, TypeError):
        delta = 3.0

    print(f"🌡️  Zone LCZ — dimension={dimension}, delta={delta}°C")

    # --- Conversion en profil VER/BUR/VHR ---
    ver, bur, vhr = dimension_to_lcz(dimension, delta)
    print(f"📊 Profil thermique — VER={ver}%, BUR={bur}%, VHR={vhr}%")

    # --- Calcul du score ---
    score = calcul_score(ver, bur, vhr)
    print(f"🎯 Score d'alerte : {score}/100 → {get_barometre(score)}")
    print(f"{'='*50}\n")

    # --- Recommandations ---
    recos_brutes = get_recommandation(score, ver, bur, vhr)

    # --- Aléa Argile RGA ---
    alea = check_risque_argile(point.y, point.x)

    # --- Simulation financière (reproductible par école) ---
    random.seed(str(row['nom']))
    surf = random.randint(800, 2000)
    val_cout = surf * 150
    val_eco = (val_cout * 0.15) + (score * 40)
    val_bilan = val_eco - (val_cout * 0.02)

    # --- Filtrage recommandations selon le profil utilisateur ---
    if categorie == "pro":
        f_recos = {
            "🏗️ Infrastructure": recos_brutes["decideurs"],
            "🏫 Vie Scolaire": recos_brutes["ecole"],
        }
    else:
        f_recos = {
            "🧒 Familles": recos_brutes["familles"],
            "📢 Citoyens": recos_brutes["citoyens"],
        }

    return {
        "nom": row["nom"],
        "adresse": str(row.get("adresse", "Bordeaux Métropole")),
        "score_alerte": score,
        "barometre": get_barometre(score),
        "recommandation": f_recos,
        "alea_argile": alea,
        "details_stats": {
            "Veg": ver,
            "Bati": bur,
            "Bitume": vhr,
            "Delta_thermique": delta,
            "Dimension_LCZ": dimension,
        },
        "surface": float(surf),
        "cout_estime": float(val_cout),
        "investissement": float(val_cout),
        "economie": float(val_eco),
        "bilan": float(val_bilan),
    }


@app.get("/diagnostic/simulation/{ecole_name}")
async def simulation(ecole_name: str, categorie: str = "public"):
    """Alias de /diagnostic/recherche pour compatibilité frontend."""
    return await diagnostic(ecole_name, categorie)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
