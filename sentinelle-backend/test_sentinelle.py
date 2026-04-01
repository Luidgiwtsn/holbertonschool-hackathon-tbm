from analysis import calcul_score, get_barometre, get_recommandation

def test_sentinelle():
    # Liste de scénarios de test (VER, BUR, VHR)
    scenarios = [
        {"nom": "École Oasis (Prévu VERT)", "ver": 80, "bur": 10, "vhr": 15},
        {"nom": "École Mitoyenne (Prévu ORANGE)", "ver": 40, "bur": 50, "vhr": 5},
        {"nom": "École Bitume (Prévu ROUGE)", "ver": 5, "bur": 90, "vhr": 0},
    ]

    print("="*60)
    print("🚀 TEST DU SYSTÈME DE DIAGNOSTIC SENTINELLE")
    print("="*60)

    for s in scenarios:
        score = calcul_score(s["ver"], s["bur"], s["vhr"])
        couleur = get_barometre(score)
        reco = get_recommandation(score, s["ver"], s["bur"], s["vhr"])

        print(f"\n📍 ECOLE : {s['nom']}")
        print(f"📊 Score : {score} | Alerte : {couleur}")
        print("-" * 30)
        print(reco)
        print("\n" + "="*60)

if __name__ == "__main__":
    test_sentinelle()
