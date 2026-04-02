from pydantic import BaseModel
from typing import Dict, List

class DiagnosticResponse(BaseModel):
    """
    Modèle de données pour la réponse de l'API Sentinelle.
    Définit la structure JSON envoyée au front-end (script.js).
    """
    nom: str
    score_alerte: float
    barometre: str
    # Structure attendue : {"Profil": ["Reco 1", "Reco 2", ...]}
    recommandation: Dict[str, List[str]]
    # Valeur par défaut si la donnée spatiale échoue
    alea_argile: str = "Non répertorié"

    class Config:
        # Permet l'affichage propre dans la documentation Swagger (/docs)
        schema_extra = {
            "example": {
                "nom": "École Pasteur",
                "score_alerte": 75.5,
                "barometre": "ROUGE",
                "recommandation": {
                    "🧒 Santé & Familles": ["Hydratation", "Vêtements clairs"],
                    "📢 Engagement": ["Signalement zones de chaleur"]
                },
                "alea_argile": "Fort"
            }
        }
