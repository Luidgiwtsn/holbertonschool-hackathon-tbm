import geopandas as gpd
from shapely.geometry import Point

# 🔥 Chargement argile
try:
    gdf_argile = gpd.read_file('ri_alearga_s.geojson')
    if gdf_argile.crs != "EPSG:4326":
        gdf_argile = gdf_argile.to_crs("EPSG:4326")
except Exception as e:
    print(f"Erreur chargement GeoJSON: {e}")
    gdf_argile = None


# 🧱 RISQUE ARGILE
def check_risque_argile(lat, lon):
    if gdf_argile is None:
        return "Inconnu"

    point = Point(lon, lat)
    zones = gdf_argile[gdf_argile.contains(point)]

    if not zones.empty:
        return zones.iloc[0].get('niv_alea', 'Présence d\'argile')

    return "Faible/Nul"


# 🔥 NOUVEAU SCORE basé LCZ (REMPLACE ton ancien calcul)
def calcul_score(lcz, alea_argile):
    """
    Score basé sur :
    - LCZ (chaleur réelle carte)
    - Argile (bonus risque)
    """

    # 🔥 SCORE CHALEUR (principal)
    if lcz >= 9:
        score = 90
    elif lcz >= 7:
        score = 75
    elif lcz >= 5:
        score = 60
    elif lcz >= 3:
        score = 40
    else:
        score = 20

    # 🧱 BONUS ARGILE (augmente le risque)
    if isinstance(alea_argile, str):
        alea = alea_argile.lower()

        if "fort" in alea or "3" in alea:
            score += 15
        elif "moyen" in alea or "2" in alea:
            score += 10

    return min(100, score)


# 📊 BAROMETRE
def get_barometre(score):
    if score >= 70:
        return "ROUGE"
    elif score >= 40:
        return "ORANGE"
    else:
        return "VERT"


# 📋 RECOMMANDATIONS (TON CODE INTACT)
def get_recommandation(score, ver=None, bur=None, vhr=None):

    infra = [] ; ecole = [] ; famille = [] ; public = []

    # 🔴 ROUGE
    if score > 70:
        infra = [
            "1. DÉCROUTAGE : Retrait de 50% de l'asphalte pour retrouver la pleine terre.",
            "2. STABILISATION RGA : Créer des noues d'infiltration pour hydrater l'argile.",
            "3. MICRO-FORÊT : Plantation Miyawaki.",
            "4. COOL ROOF : Toits blancs.",
            "5. SOLS VIVANTS : matériaux naturels.",
            "6. OMBRE BIOCLIMATIQUE.",
            "7. RÉSERVES HYDRIQUES."
        ]
        ecole = [
            "1. Récréations matinales.",
            "2. Oyats.",
            "3. Paillage.",
            "4. Réutilisation eau.",
            "5. Ventilation nocturne.",
            "6. Bassinage.",
            "7. Élèves ambassadeurs."
        ]
        famille = [
            "1. Hydratation régulière.",
            "2. Vêtements adaptés.",
            "3. Surveillance chaleur."
        ]
        public = [
            "1. Halte fraîcheur.",
            "2. Sensibilisation.",
            "3. Implication quartier."
        ]

    # 🟠 ORANGE
    elif score > 40:
        infra = ["Albédo clair", "Murs végétalisés", "Voiles d'ombrage"]
        ecole = ["Classe dehors", "Arrosage", "Stores fermés"]
        famille = ["Crème solaire", "Chapeau", "Hydratation"]
        public = ["Végétalisation", "Guide fraîcheur"]

    # 🟢 VERT
    else:
        infra = ["Entretien arbres", "Compost", "Biodiversité"]
        ecole = ["Jardinage", "Cours dehors"]
        famille = ["Habitudes saines"]
        public = ["Sensibilisation"]

    return {
        "decideurs": infra,
        "ecole": ecole,
        "familles": famille,
        "citoyens": public
    }