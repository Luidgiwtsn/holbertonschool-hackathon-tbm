import geopandas as gpd
from shapely.geometry import Point
import os

# --- INITIALISATION SÉCURISÉE ---
# On déclare la variable globale mais on ne charge pas ici pour éviter les blocages au démarrage
gdf_argile = None

def load_argile_data():
    """Fonction appelée au démarrage du serveur (main.py) pour charger les données une seule fois"""
    global gdf_argile
    base_dir = os.path.dirname(__file__)
    geojson_path = os.path.join(base_dir, 'data', 'ri_alearga_s.geojson')
    
    if os.path.exists(geojson_path):
        try:
            gdf_argile = gpd.read_file(geojson_path)
            # Conversion systématique en WGS84 pour correspondre aux coordonnées GPS du front
            if gdf_argile.crs != "EPSG:4326":
                gdf_argile = gdf_argile.to_crs("EPSG:4326")
            # Normalisation des noms de colonnes en minuscules pour éviter les erreurs de saisie
            gdf_argile.columns = [c.lower() for c in gdf_argile.columns]
            print("✅ Base Argile (RGA) chargée avec succès")
        except Exception as e:
            print(f"❌ Erreur lecture GeoJSON Argile: {e}")
            gdf_argile = None
    else:
        print("⚠️ Fichier ri_alearga_s.geojson introuvable dans /data")

def check_risque_argile(lat, lon):
    """Vérifie l'aléa RGA pour un point donné"""
    global gdf_argile
    if gdf_argile is None or gdf_argile.empty:
        return "Donnée indisponible"
    
    try:
        point = Point(lon, lat)
        # On cherche l'intersection
        match = gdf_argile[gdf_argile.geometry.contains(point)]
        
        if not match.empty:
            # On cherche les noms de colonnes courants (niv_alea ou alea)
            for col in ['niv_alea', 'alea', 'classe']:
                if col in match.columns:
                    return str(match.iloc[0][col])
            return "Zone identifiée"
        return "Faible/Nul"
    except Exception:
        return "Erreur analyse spatiale"

def calcul_score(ver, bur, vhr):
    """
    Scoring Sentinelle :
    Plus le bâti (bur) et le bitume (vhr) sont hauts, plus le score d'alerte monte.
    La végétation (ver) réduit le score.
    """
    # On s'assure que les entrées sont des nombres
    ver, bur, vhr = float(ver), float(bur), float(vhr)
    
    # Formule équilibrée pour le pitch
    score = (100 - ver) + (bur * 0.5) + (vhr * 0.5) 
    # On divise par 1.5 pour ramener sur une base ~100
    score_final = score / 1.5
    
    return max(0, min(100, round(score_final, 1)))

def get_barometre(score):
    if score > 70: return "ROUGE"
    elif score > 40: return "ORANGE"
    else: return "VERT"

def get_recommandation(score, ver, bur, vhr):
    """Diagnostic 7x4 Bordeaux Métropole."""
    infra = [] ; ecole = [] ; famille = [] ; public = []

    if score > 70:
        infra = [
            "1. DÉCROUTAGE : Retrait de 50% de l'asphalte pour retrouver la pleine terre.",
            "2. STABILISATION RGA : Créer des noues d'infiltration pour hydrater l'argile.",
            "3. MICRO-FORÊT : Plantation 'Miyawaki' (3 arbres/m²) pour la fraîcheur.",
            "4. COOL ROOF : Revêtement blanc réflectif sur les toits.",
            "5. SOLS VIVANTS : Pavés enherbés ou bois en remplacement du bitume.",
            "6. OMBRE BIOCLIMATIQUE : Pergolas végétalisées sur les façades.",
            "7. RÉSERVES HYDRIQUES : Cuves pour compenser le déficit hydrique des sols."
        ]
        ecole = [
            "1. RYTHME : Récréations matinales et repli au frais l'après-midi.",
            "2. OYATS : Jarres d'irrigation enterrées pour stabiliser l'argile.",
            "3. PAILLAGE : 15cm de broyat bois contre la rétractation argileuse.",
            "4. EAUX GRISES : Réutiliser l'eau des lavabos pour les fondations.",
            "5. FREE-COOLING : Ventilation nocturne forcée (3h-6h).",
            "6. BASSINAGE : Humidifier les feuillages pour saturer l'air en fraîcheur.",
            "7. AMBASSADEURS : Élèves responsables du suivi de l'humidité."
        ]
        famille = [
            "1. RASSURANCE : Bulletin 'Confort' pour apaiser l'anxiété.",
            "2. VENTURI : Humidifier les avant-bras pour refroidir le sang.",
            "3. DRESS-CODE : Fibres naturelles (coton/lin) et nuque couverte.",
            "4. HYDRATATION : Protocole 'petite gorgée' toutes les 20 min.",
            "5. SLOW MOTION : Ralentir les jeux pour limiter la surchauffe.",
            "6. RÉCUPÉRATION : Douche tiède (30°C) au retour à la maison.",
            "7. VIGILANCE : Observer les signes de fatigue ou d'apathie."
        ]
        public = [
            "1. HALTE FRAÎCHEUR : Ouvrir la cour aux seniors isolés (pics de chaleur).",
            "2. SIGNALÉTIQUE : Panneaux expliquant le lien entre végétal et RGA.",
            "3. DATA-PARTAGE : QR Code pour consulter le score thermique en direct.",
            "4. CHANTIER : Impliquer les riverains dans les plantations.",
            "5. ARROSAGE : Réseau de voisins pour veiller sur le parc en vacances.",
            "6. ÉCO-CIVISME : Campagne 'Moteur Coupé' aux abords de l'école.",
            "7. HUB : Faire de l'école le modèle de résilience du quartier."
        ]
    elif score > 40:
        infra = ["1. Albédo clair.", "2. Murs de lierre.", "3. Puits perdus.", "4. Bancs pierre.", "5. Sondes humidité.", "6. Voiles d'ombrage.", "7. Noues drainantes."]
        ecole = ["1. Classe dehors.", "2. Bassinage.", "3. Oyats.", "4. Collecte eaux gourdes.", "5. Ateliers eau.", "6. Stores fermés dès 8h.", "7. Ventilation pauses."]
        famille = ["1. Crème solaire.", "2. Chemin de l'ombre.", "3. Douche tiède.", "4. Volets fermés.", "5. Moment calme.", "6. Eau tempérée.", "7. Chapeau."]
        public = ["1. Végétaliser balcons.", "2. Challenge Zéro Bitume.", "3. Guide fraîcheur.", "4. Fête nature.", "5. Brigade arrosage.", "6. Info RGA.", "7. Lien seniors."]
    else:
        infra = ["1. Taille douce.", "2. Compost argile.", "3. Nichoirs.", "4. Veille fondations.", "5. Récupérateurs pluie.", "6. Passages faune.", "7. Tons clairs."]
        ecole = ["1. École forêt.", "2. Potager.", "3. Gestion irrigation.", "4. Compostage.", "5. Relevés météo.", "6. Accueil classes rouges.", "7. Carnet de l'arbre."]
        famille = ["1. Éducation.", "2. Sorties parcs.", "3. Économie eau.", "4. Vélo ombre.", "5. Impact cognitif.", "6. Parents Oasis.", "7. Vigilance santé."]
        public = ["1. Vitrine mairies.", "2. Inspiration riverains.", "3. Trame verte.", "4. Fierté agents.", "5. Don de graines.", "6. Veille fuites.", "7. Nuit fraîcheur."]

    return {
        "decideurs": infra,
        "ecole": ecole,
        "familles": famille,
        "citoyens": public
    }
