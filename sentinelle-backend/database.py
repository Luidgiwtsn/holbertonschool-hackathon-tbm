# database.py
import geopandas as gpd

def charger_donnees():
    """
    Charge les données des écoles et des zones LCZ
    """
    ecoles = gpd.read_file("data/ecoles_bordeaux.geojson")
    zones = gpd.read_file("data/lcz_data.geojson")

    # Assurer la même projection
    ecoles = ecoles.to_crs(zones.crs)

    return ecoles, zones
