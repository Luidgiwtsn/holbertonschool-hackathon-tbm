import geopandas as gpd
from shapely.geometry import Point

# Chargement global de la base de données argile
try:
    gdf_argile = gpd.read_file('ri_alearga_s.geojson')
    # On s'assure que le système de coordonnées est en WGS84 (GPS standard)
    if gdf_argile.crs != "EPSG:4326":
        gdf_argile = gdf_argile.to_crs("EPSG:4326")
except Exception as e:
    print(f"Erreur chargement GeoJSON: {e}")
    gdf_argile = None

def check_risque_argile(lat, lon):
    """Vérifie si les coordonnées GPS tombent dans une zone d'aléa Fort ou Moyen"""
    if gdf_argile is None: return "Inconnu"
    
    point = Point(lon, lat)
    # On regarde l'intersection entre le point de l'école et les polygones d'argile
    zones = gdf_argile[gdf_argile.contains(point)]
    
    if not zones.empty:
        # 'niv_alea' est souvent le nom de colonne dans les fichiers TBM/BRGM
        return zones.iloc[0].get('niv_alea', 'Présence d\'argile')
    return "Faible/Nul"

def calcul_score(ver, bur, vhr):
    """ TON SCORING ORIGINAL (Inchangé) """
    score = (100 - ver) + (bur * 0.5) - (vhr * 2)
    return max(0, min(100, round(score, 1)))

def get_barometre(score):
    if score > 70: return "ROUGE"
    elif score > 40: return "ORANGE"
    else: return "VERT"

def get_recommandation(score, ver, bur, vhr):
    """
    Diagnostic 7x4 Bordeaux Métropole.
    Focus : Îlot de Chaleur, RGA (Argiles) et Transmission Citoyenne.
    """
    infra = [] ; ecole = [] ; famille = [] ; public = []

    # --- CAS ROUGE (> 70) : URGENCE & RÉHABILITATION ---
    if score > 70:
        infra = [
            "1. DÉCROUTAGE : Retrait de 50% de l'asphalte pour retrouver la pleine terre.",
            "2. STABILISATION RGA : Créer des noues d'infiltration pour hydrater l'argile et éviter les fissures.",
            "3. MICRO-FORÊT : Plantation 'Miyawaki' (3 arbres/m²) pour un dôme de fraîcheur naturel.",
            "4. COOL ROOF : Revêtement blanc réflectif sur les toits pour casser l'absorption de chaleur.",
            "5. SOLS VIVANTS : Pavés enherbés ou bois (matériaux à faible inertie) en remplacement du bitume.",
            "6. OMBRE BIOCLIMATIQUE : Pergolas végétalisées pour protéger les façades du rayonnement.",
            "7. RÉSERVES HYDRIQUES : Cuves de 10m3 pour compenser le déficit hydrique des sols."
        ]
        ecole = [
            "1. RYTHME : Récréations matinales et repli en salles fraîches l'après-midi.",
            "2. OYATS : Jarres d'irrigation enterrées pour un arrosage profond stabilisant l'argile.",
            "3. PAILLAGE : 15cm de broyat bois pour empêcher la rétractation argileuse.",
            "4. EAUX GRISES : Réutiliser l'eau des lavabos pour humidifier les fondations.",
            "5. FREE-COOLING : Ventilation nocturne forcée (3h-6h) pour évacuer les calories des murs.",
            "6. BASSINAGE : Humidifier les feuillages à 11h pour saturer l'air en fraîcheur.",
            "7. AMBASSADEURS : Élèves responsables du suivi de l'humidité et du bien-être végétal."
        ]
        famille = [
            "1. RASSURANCE : Bulletin 'Confort' pour apaiser l'anxiété des familles.",
            "2. VENTURI : Humidifier les avant-bras pour refroidir le sang circulant.",
            "3. DRESS-CODE : Fibres naturelles (coton/lin), casquette et nuque couverte.",
            "4. HYDRATATION : Gourde isotherme et protocole 'petite gorgée' toutes les 20 min.",
            "5. SLOW MOTION : Ralentir les jeux pour limiter la surchauffe interne.",
            "6. RÉCUPÉRATION : Douche tiède (30°C) au retour pour la baisse thermique.",
            "7. VIGILANCE : Observer les urines foncées ou l'apathie (signes de déshydratation)."
        ]
        public = [
            "1. HALTE FRAÎCHEUR : Ouvrir la cour aux seniors isolés pendant les pics de chaleur.",
            "2. SIGNALÉTIQUE : Panneaux expliquant le lien entre végétal et protection des bâtiments (RGA).",
            "3. DATA-PARTAGE : QR Code sur le portail pour consulter le score thermique en direct.",
            "4. CHANTIER : Impliquer les riverains dans les plantations (lien nature-quartier).",
            "5. ARROSAGE : Réseau de voisins pour veiller sur le parc durant les vacances.",
            "6. ÉCO-CIVISME : Campagne 'Moteur Coupé' aux abords pour réduire l'ozone.",
            "7. HUB : Faire de l'école le modèle de résilience contre le retrait des argiles."
        ]

    # --- CAS ORANGE (40-70) : VIGILANCE & AMÉLIORATION ---
    elif score > 40:
        infra = ["1. Albédo clair.", "2. Murs de lierre.", "3. Puits perdus.", "4. Bancs pierre.", "5. Sondes humidité.", "6. Voiles d'ombrage.", "7. Noues drainantes."]
        ecole = ["1. Classe dehors.", "2. Bassinage.", "3. Oyats.", "4. Collecte eaux gourdes.", "5. Ateliers eau.", "6. Stores fermés dès 8h.", "7. Ventilation pauses."]
        famille = ["1. Crème solaire.", "2. Chemin de l'ombre.", "3. Douche tiède.", "4. Volets fermés.", "5. Moment calme.", "6. Eau tempérée.", "7. Chapeau."]
        public = ["1. Végétaliser balcons.", "2. Challenge Zéro Bitume.", "3. Guide fraîcheur.", "4. Fête nature.", "5. Brigade arrosage.", "6. Info RGA.", "7. Lien seniors."]

    # --- CAS VERT (< 40) : PROTECTION & TRANSMISSION ---
    else:
        infra = [
            "1. PÉRENNISATION : Taille douce des arbres pour maintenir une ombre portée maximale.",
            "2. SOLS : Apport régulier de compost pour maintenir la porosité et l'humidité des argiles.",
            "3. BIODIVERSITÉ : Installation de nichoirs et d'hôtels à insectes (équilibre écosystémique).",
            "4. VEILLE BÂTI : Inspection annuelle des fondations pour prévenir tout micro-retrait d'argile.",
            "5. OPTIMISATION : Installation de récupérateurs d'eau de pluie pour l'autonomie du jardin.",
            "6. CONNECTIVITÉ : Créer des passages pour la petite faune (hérissons) entre les zones vertes.",
            "7. MATÉRIAUX : Remplacer progressivement les derniers éléments sombres par des tons clairs."
        ]
        ecole = [
            "1. ÉCOLE DE LA FORÊT : Généraliser les cours en extérieur pour le bien-être cognitif.",
            "2. JARDINAGE : Entretenir le potager avec les enfants (notion de cycle de vie).",
            "3. GESTION EAU : Maintenance des systèmes d'irrigation économes (Oyats, goutte-à-goutte).",
            "4. TRI : Compostage des déchets de cantine pour nourrir les sols de l'école.",
            "5. OBSERVATION : Relever les températures avec les élèves pour comprendre l'effet 'Oasis'.",
            "6. PARTAGE : Accueillir d'autres classes de zones 'Rouges' pour des activités fraîches.",
            "7. ARCHIVAGE : Tenir un carnet de santé de l'arbre (croissance, santé, ombre)."
        ]
        famille = [
            "1. ÉDUCATION : Transmettre les bons réflexes (hydratation, vêtements) comme des habitudes de vie.",
            "2. NATURE : Encourager les sorties en famille dans les parcs pour renforcer le lien au vivant.",
            "3. ÉCO-GESTE : Sensibiliser à l'économie d'eau domestique pour préserver les nappes locales.",
            "4. MOBILITÉ : Privilégier le vélo ou la marche à l'ombre pour venir à l'école.",
            "5. BIEN-ÊTRE : Noter l'impact positif de la verdure sur la concentration de l'enfant.",
            "6. PARTICIPATION : S'impliquer dans l'association des parents pour protéger la cour Oasis.",
            "7. SANTÉ : Garder une vigilance sur l'hydratation même quand le ressenti est agréable."
        ]
        public = [
            "1. VITRINE : Faire de l'école un lieu de visite pour d'autres mairies de la Métropole.",
            "2. INSPIRATION : Inciter les riverains à copier les essences d'arbres résilientes de l'école.",
            "3. RÉSEAU : Intégrer l'école dans la 'Trame Verte' de Bordeaux Métropole.",
            "4. FIERTÉ : Valoriser le travail des agents d'entretien et des jardiniers de la ville.",
            "5. PARTAGE : Distribuer des graines issues du jardin de l'école aux habitants du quartier.",
            "6. VEILLE : Signaler toute fuite d'eau ou dépérissement végétal aux abords de l'école.",
            "7. ÉVÈNEMENT : Organiser une 'Nuit de la Fraîcheur' pour observer la biodiversité nocturne."
        ]

    # reponse format .json
    return {
        "decideurs": infra,
        "ecole": ecole,
        "familles": famille,
        "citoyens": public
    }