# models.py
from pydantic import BaseModel
from typing import Dict, List

class Diagnostic(BaseModel):
    nom: str
    score_alerte: float
    barometre: str
    recommandation: Dict[str, List[str]]
    alea_argile: str = "Non répertorié"