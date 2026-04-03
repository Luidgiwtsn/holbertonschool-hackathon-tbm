import geopandas as gpd
import os
from unidecode import unidecode

def charger_donnees():
    """
    Charge les données des écoles et des zones LCZ.
    Retourne un tuple (ecoles, zones), avec None si échec.
    """
    base_path = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_path, "data")

    file_ecoles = os.path.join(data_dir, "export.geojson")
    file_zones = os.path.join(data_dir, "lcz_bordeaux.geojson")

    try:
        # --- 1. Chargement des écoles ---
        if not os.path.exists(file_ecoles):
            print(f"❌ FICHIER MANQUANT : {file_ecoles}")
            return None, None

        ecoles = gpd.read_file(file_ecoles).to_crs(epsg=4326)
        print(f"✅ Écoles chargées : {len(ecoles)} points.")

        # Normalisation du nom de colonne principal
        col_nom = next(
            (c for c in ['name', 'nom', 'NOM', 'libelle'] if c in ecoles.columns),
            ecoles.columns[0]
        )
        ecoles = ecoles.rename(columns={col_nom: 'nom'})

        # Normalisation de la colonne adresse si elle existe
        col_adr = next(
            (c for c in ['adresse', 'address', 'ADR', 'ADRESSE'] if c in ecoles.columns),
            None
        )
        if col_adr and col_adr != 'adresse':
            ecoles = ecoles.rename(columns={col_adr: 'adresse'})

        # Colonne de recherche sans accents et en majuscules
        ecoles['NOM_RECHERCHE'] = (
            ecoles['nom']
            .astype(str)
            .apply(lambda x: unidecode(x).upper().strip())
        )

        # --- 2. Chargement des zones thermiques LCZ ---
        if not os.path.exists(file_zones):
            print(f"❌ FICHIER MANQUANT : {file_zones}")
            return ecoles, None

        zones = gpd.read_file(file_zones).to_crs(epsg=4326)

        # Normalisation des noms de colonnes en minuscules
        zones.columns = [c.lower().strip() for c in zones.columns]

        print(f"✅ Zones LCZ chargées : {len(zones)} polygones.")
        print(f"📊 Colonnes LCZ : {list(zones.columns)}")

        return ecoles, zones

    except Exception as e:
        print(f"❌ ERREUR CRITIQUE DATABASE : {e}")
        return None, None
