#!/bin/bash

# Liste des écoles
ecoles=("Lycée technologique Saint-Louis" "Lycée Jean Moulin" "Collège Victor Hugo")

for ecole in "${ecoles[@]}"; do
    # Encode le nom pour l'URL
    ecole_url=$(python3 -c "import urllib.parse; print(urllib.parse.quote('''$ecole'''))")
    # Appelle l'API et formate le JSON
    echo "🔹 $ecole"
    curl -s "http://127.0.0.1:8000/diagnostic/$ecole_url" | python3 -m json.tool
    echo
done
