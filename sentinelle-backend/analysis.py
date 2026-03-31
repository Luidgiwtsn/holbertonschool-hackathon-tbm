# analysis.py
"""
Cœur du backend Sentinelle Écoles :
- calcul du score de vulnérabilité
- baromètre couleur (Vert / Orange / Rouge)
- recommandations concrètes
"""

def calcul_score(ver, bur, vhr):
    """
    Calcule un score de risque basé sur :
    - VER : végétation (%)
    - BUR : bâti (%)
    - VHR : hauteur végétation (m)
    Score compris entre 0 et 100
    """
    score = (100 - ver) + (bur * 0.5) - (vhr * 2)
    return max(0, min(100, round(score, 1)))  # borne entre 0 et 100

def get_barometre(score):
    """
    Transforme le score en baromètre couleur
    """
    if score > 70:
        return "ROUGE"
    elif score > 40:
        return "ORANGE"
    else:
        return "VERT"

def get_recommandation(score, ver, bur, vhr):
    """
    Génère une recommandation concrète selon le score et les valeurs
    """
    recommandations = []

    if score > 70:
        if ver < 30:
            recommandations.append("Planter des arbres ou créer des espaces verts")
        if bur > 50:
            recommandations.append("Désimperméabiliser les sols, installer zones ombragées")
        if vhr < 5:
            recommandations.append("Installer pergolas ou zones fraîches")
        if not recommandations:
            recommandations.append("Surveiller et maintenir l'école fraîche")
    elif score > 40:
        recommandations.append("Plantations ponctuelles et aménagements légers pour réduire la chaleur")
    else:
        recommandations.append("École bien protégée, maintenir les aménagements existants")

    return " ; ".join(recommandations)
