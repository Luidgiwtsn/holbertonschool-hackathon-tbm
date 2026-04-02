from fastapi import FastAPI, HTTPException, Query
from unidecode import unidecode
from database import charger_donnees
from analysis import calcul_score, get_barometre, get_recommandation
from models import Diagnostic
import pandas as pd
import uvicorn
import geopandas as gpd
import os
from enum import Enum

# --- 1. DÉFINITION DU PARCOURS UTILISATEUR (ENTONNOIR) ---
class ProfilUtilisateur(str, Enum):
    public = "public"  # Parcours : Familles, Parents, Riverains
    pro = "pro"        # Parcours : Mairies, Élus, Services Techniques

# Initialisation de l'API
app = FastAPI(
    title="Sentinelle Écoles API", 
    description="Plateforme de résilience climatique pour les établissements scolaires",
    version="1.5.0"
)

# --- 2. VARIABLES GLOBALES & CHARGEMENT ---
ecoles = None
zones = None
argile = None 

def initialiser_systeme():
    global ecoles, zones, argile
    try:
        ecoles, zones = charger_donnees()
        base_dir = os.path.dirname(__file__)
        geojson_path = os.path.join(base_dir, 'data', 'ri_alearga_s.geojson')
        
        if os.path.exists(geojson_path):
            argile = gpd.read_file(geojson_path).to_crs(epsg=4326)
            argile.columns = [c.lower() for c in argile.columns]
            print("✅ GÉO-DONNÉES ARGILE : Chargées")
        
        if ecoles is not None:
            if not isinstance(ecoles, gpd.GeoDataFrame):
                ecoles = gpd.GeoDataFrame(ecoles, geometry=gpd.points_from_xy(ecoles.lon, ecoles.lat))
            ecoles = ecoles.to_crs(epsg=4326)

            # Nettoyage des types pour éviter le "NAN"
            colonnes_type = ['school:FR', 'amenity', 'description']
            for col in colonnes_type:
                if col in ecoles.columns:
                    ecoles[col] = ecoles[col].astype(str).replace(['nan', 'None', 'NaN'], 'Établissement')

            # Indexation pour la recherche textuelle
            col_nom = "name" if "name" in ecoles.columns else ecoles.columns[0]
            ecoles["nom_normalise"] = ecoles[col_nom].apply(
                lambda x: unidecode(str(x)).lower().strip() if pd.notnull(x) else ""
            )
        print("🚀 Backend Sentinelle opérationnel.")
    except Exception as e:
        print(f"❌ Erreur Initialisation : {e}")

initialiser_systeme()

# --- 3. ANALYSE SPATIALE ---

def get_alea_argile(point_ecole):
    """Détection du risque géologique par tampon (buffer) de 50m."""
    if argile is None or argile.empty: return "Indisponible"
    gdf_ecole = gpd.GeoDataFrame(geometry=[point_ecole], crs="EPSG:4326").to_crs(epsg=3857)
    buffer_50m = gdf_ecole.buffer(50).to_crs(epsg=4326).iloc[0]
    match = argile[argile.geometry.intersects(buffer_50m)]
    if not match.empty:
        col_alea = 'alea' if 'alea' in match.columns else match.columns[0]
        return ", ".join(match[col_alea].astype(str).unique())
    return "Faible/Nul"

# --- 4. ENDPOINTS (LOGIQUE MÉTIER) ---

@app.get("/", tags=["Système"])
def accueil():
    """Accueil et orientation de l'utilisateur."""
    return {
        "projet": "Sentinelle Écoles",
        "statut": "En ligne",
        "action_requise": "Veuillez choisir un profil (?categorie=pro ou ?categorie=public) pour vos recherches."
    }

@app.get("/diagnostic/recherche/{ecole_name}", response_model=Diagnostic, tags=["Diagnostic"])
def diagnostic(
    ecole_name: str, 
    categorie: ProfilUtilisateur = Query(..., description="Filtre les recommandations selon le profil")
):
    """Effectue un diagnostic structuré en JSON selon l'entonnoir utilisateur."""
    nom_cherche = unidecode(ecole_name).lower().strip()
    match = ecoles[ecoles["nom_normalise"].str.contains(nom_cherche)]
    
    if match.empty: 
        raise HTTPException(status_code=404, detail="Établissement non référencé")

    ecole_row = match.iloc[0]
    z_match = zones[zones.geometry.contains(ecole_row.geometry)]
    
    # Données climatiques
    ver = float(z_match.iloc[0].get("VER", 0)) if not z_match.empty else 0.0
    bur = float(z_match.iloc[0].get("BUR", 100)) if not z_match.empty else 100.0
    vhr = float(z_match.iloc[0].get("VHR", 0)) if not z_match.empty else 0.0

    score = calcul_score(ver, bur, vhr)
    alea_rga = get_alea_argile(ecole_row.geometry)
    
    # --- GÉNÉRATION ET FILTRAGE JSON ---
    reco_dict = get_recommandation(score, ver, bur, vhr)
    reco_finale = {}

    if categorie == ProfilUtilisateur.pro:
        # Profil Décideurs / Technique
        reco_finale["🏗️ infrastructure_mairie"] = reco_dict["decideurs"]
        reco_finale["🏫 gestion_etablissement"] = reco_dict["ecole"]
        # Alerte technique spécifique RGA
        if any(x in alea_rga.lower() for x in ["fort", "moyen", "2", "3"]):
            reco_finale["alertes_techniques"] = [f"🚨 RISQUE GÉOLOGIQUE : Aléa RGA détecté ({alea_rga})."]
    else:
        # Profil Familles / Public
        reco_finale["🧒 sante_et_familles"] = reco_dict["familles"]
        reco_finale["📢 engagement_citoyen"] = reco_dict["citoyens"]

    return Diagnostic(
        nom=str(ecole_row.get("name")),
        score_alerte=round(score, 2),
        barometre=get_barometre(score),
        recommandation=reco_finale,
        alea_argile=alea_rga
    )
#simulateur d'action et de cout
@app.get("/diagnostic/simulation/{ecole_name}", tags=["Simulation"])
def simulation(ecole_name: str, projet_veg: float = Query(30.0, ge=0, le=100)):
    """Simulateur de ROI pour la végétalisation."""
    nom_cherche = unidecode(ecole_name).lower().strip()
    match = ecoles[ecoles["nom_normalise"].str.contains(nom_cherche)]
    if match.empty: raise HTTPException(status_code=404)
    
    ecole_info = match.iloc[0]
    alea = get_alea_argile(ecole_info.geometry).lower()
    type_ecole = str(ecole_info.get('school:FR', 'Établissement')).lower()
    
    # Calcul des surfaces types
    surfaces = {"lycee": 2500, "college": 1800, "maternelle": 700, "kindergarten": 400}
    surface_ref = 1000 
    for k, v in surfaces.items():
        if k in type_ecole:
            surface_ref = v
            break

    surface_a_traiter = (surface_ref * 1.2) * (projet_veg/100)
    cout = surface_a_traiter * 150 
    gain = (surface_ref * 50) if any(x in alea for x in ["fort", "3", "moyen", "2"]) else 0
    bilan = gain - cout

    return {
        "ecole": ecole_info.get("name"),
        "profil_risque": "STRUCTUREL (Argile)" if gain > 0 else "THERMIQUE (Canicule)",
        "simulation": {
            "surface_renaturee": f"{round(surface_a_traiter, 1)} m²",
            "investissement_estime": f"{round(cout, 2)} €",
            "economie_reparation_evitee": f"{round(gain, 2)} €",
            "bilan_net_20_ans": f"{round(bilan, 2)} €"
        },
        "conclusion": "INVESTISSEMENT RENTABLE" if bilan > 0 else "DÉPENSE SANTÉ PUBLIQUE"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
