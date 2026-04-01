# models.py
from pydantic import BaseModel

class Diagnostic(BaseModel):
    nom: str
    score_alerte: float
    barometre: str
    recommandation: str
    alea_argile: str = "Non répertorié" # Le champ qui manquait
