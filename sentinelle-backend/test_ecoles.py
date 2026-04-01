import requests

ecoles = [
    "Lycée technologique Saint-Louis",
    "Lycée Jean Moulin",
    "Collège Victor Hugo"
]

url_base = "http://127.0.0.1:8000/diagnostic/"

for ecole in ecoles:
    response = requests.get(url_base + ecole)
    if response.status_code == 200:
        data = response.json()
        print(f"🔹 {ecole}")
        print(data)
    else:
        print(f"❌ {ecole} : {response.status_code}")
    print()
