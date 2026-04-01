import requests

def tester_sentinelle_S(nom_ecole):
    base_url = "http://127.0.0.1:8000/diagnostic/recherche/"
    sim_url = "http://127.0.0.1:8000/diagnostic/simulation/"
    
    print("\n" + "="*60)
    print(f"🚀 TEST SYSTÈME  : {nom_ecole}")
    print("="*60)
    
    try:
        # 1. Test du Diagnostic (Chaleur + Argile avec Buffer)
        r = requests.get(f"{base_url}{nom_ecole}")
        r.raise_for_status()
        data = r.json()
        
        print(f"\n📍 ECOLE : {data['nom']}")
        print(f"🌡️  RISQUE THERMIQUE : {data['score_alerte']} / 100 ({data['barometre']})")
        print(f"🌍 ETAT DU SOL (ALEA) : {data['alea_argile']}")
        
        # 2. Test de la Simulation Financière (Clé corrigée : 'finance')
        s = requests.get(f"{sim_url}{nom_ecole}?projet_veg=30")
        s.raise_for_status()
        sim = s.json()
        fin = sim['finance'] # <--- Correction ici
        
        print("\n💰 ANALYSE FINANCIÈRE (Simulation 30% végétalisation) :")
        print(f"   - Coût estimé des travaux : {fin['cout']}")
        print(f"   - Sinistres évités (Murs)  : {fin['economie_fissures']}")
        print(f"   - BILAN DE RÉSILIENCE     : {fin['bilan']}")
        print("\n" + "="*60)

    except Exception as e:
        print(f"\n❌ ERREUR DE TEST : {e}")

if __name__ == "__main__":
    tester_sentinelle_S("Sainte-Marie")
