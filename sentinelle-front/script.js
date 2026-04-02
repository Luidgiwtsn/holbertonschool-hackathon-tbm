let schoolsData = [];
let currentProfil = "public";
let lastSelectedSchool = null; // Pour pouvoir rafraîchir si on change de profil

// 1. Chargement initial des données GéoJSON
fetch("data/export.geojson")
    .then(res => res.json())
    .then(data => {
        schoolsData = data.features;
        afficherListe(schoolsData);
    })
    .catch(err => {
        console.error("Erreur chargement export.geojson:", err);
        document.getElementById("listeEcoles").innerHTML = "❌ Erreur de chargement";
    });

// 2. Gestion du switch Profil (Public / Pro)
function setProfil(p) {
    currentProfil = p;
    document.getElementById("btn-public").classList.toggle("active", p === 'public');
    document.getElementById("btn-pro").classList.toggle("active", p === 'pro');
    
    // Si une école est déjà sélectionnée, on relance l'analyse avec le nouveau profil
    if (lastSelectedSchool) {
        handleSchoolClick(lastSelectedSchool);
    }
}

// 3. Rendu de la liste latérale
function afficherListe(data) {
    const liste = document.getElementById("listeEcoles");
    liste.innerHTML = "";
    data.forEach(s => {
        let li = document.createElement("li");
        li.textContent = s.properties.name || "École sans nom";
        li.onclick = () => handleSchoolClick(s);
        liste.appendChild(li);
    });
}

// 4. Logique principale au clic sur une école
async function handleSchoolClick(school) {
    lastSelectedSchool = school;
    const nom = school.properties.name;
    const resultDiv = document.getElementById("result");
    const [lon, lat] = school.geometry.coordinates;

    // Feedback visuel immédiat
    resultDiv.innerHTML = `<div class="loader">⏳ Analyse spatiale : ${nom}...</div>`;
    
    // Scroll automatique vers le haut du panneau de résultat
    document.getElementById("result-container").scrollTop = 0;

    // Mise à jour de la carte Felt (Zoom sur l'école)
    document.getElementById("mapFrame").src = `https://felt.com/embed/map/Untitled-Map-trd59Cqj4RuKu8WX9Cw2eYCD?loc=${lat},${lon},17z&legend=1`;

    try {
        // Appel API Backend
        const url = `http://127.0.0.1:8000/diagnostic/recherche/${encodeURIComponent(nom)}?categorie=${currentProfil}`;
        const res = await fetch(url);
        
        if (!res.ok) throw new Error("Erreur serveur");
        
        const data = await res.json();
        
        // Génération du HTML pour les recommandations (7x4)
        let recoHTML = Object.entries(data.recommandation).map(([titre, points]) => `
            <div class="reco-card">
                <h4>${titre}</h4>
                <ul>${points.map(p => `<li>${p}</li>`).join('')}</ul>
            </div>
        `).join('');

        // Affichage final
        resultDiv.innerHTML = `
            <div class="score-box ${data.barometre.toLowerCase()}">
                <h3>${data.nom}</h3>
                <p><b>Statut : ${data.barometre}</b> (${data.score_alerte}/100)</p>
            </div>
            <p class="info-text">🌍 <b>Risque Géologique (RGA) :</b> ${data.alea_argile}</p>
            <div class="reco-list">${recoHTML}</div>
            
            <button class="primary-btn" style="margin-top:15px; width:100%; background:#27ae60" 
                    onclick="runSimu('${nom.replace(/'/g, "\\'")}')">
                📊 Simulation Financière ROI
            </button>
            <div id="simu-area"></div>
        `;
    } catch (e) {
        resultDiv.innerHTML = `<div class="error-box">❌ Erreur : Impossible de joindre l'API Sentinelle. Vérifiez que le serveur Python est lancé.</div>`;
    }
}

// 5. Fonction de simulation ROI
async function runSimu(nom) {
    const area = document.getElementById("simu-area");
    area.innerHTML = "<p>🧮 Calcul des économies d'entretien...</p>";
    
    try {
        const res = await fetch(`http://127.0.0.1:8000/diagnostic/simulation/${encodeURIComponent(nom)}`);
        const d = await res.json();
        area.innerHTML = `
            <div class="simu-box">
                <p>📐 <b>Surface :</b> ${d.surface}</p>
                <p>💰 <b>Coût estimé :</b> ${d.investissement}</p>
                <p>📉 <b>Économie (RGA) :</b> ${d.economie}</p>
                <hr>
                <center><b>BILAN : ${d.bilan}</b></center>
            </div>`;
    } catch (e) {
        area.innerHTML = "⚠️ Échec de la simulation.";
    }
}

// 6. Fonction de recherche textuelle
function searchSchool() {
    const searchInput = document.getElementById("search");
    const val = searchInput.value.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
    
    if (!val) return;

    const s = schoolsData.find(x => {
        const schoolName = (x.properties.name || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
        return schoolName.includes(val);
    });

    if (s) {
        handleSchoolClick(s);
    } else {
        alert("Désolé, cet établissement n'est pas répertorié dans la base.");
    }
}
