// 🔥 Attendre que le DOM soit prêt
document.addEventListener("DOMContentLoaded", () => {

  let schoolsData = [];
  let currentSchool = null;

  // 🔤 Normalisation (évite crash si valeur vide)
  function normalize(text) {
    if (!text) return "";
    return text.toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  // 📦 Charger les écoles
  fetch("data/export.geojson")
    .then(r => r.json())
    .then(data => {
      schoolsData = data.features;
      afficherListe(schoolsData);
    })
    .catch(() => console.error("❌ Erreur chargement GeoJSON"));

  // 📋 Liste des écoles (menu gauche)
  function afficherListe(data) {
    let ul = document.getElementById("listeEcoles");
    ul.innerHTML = "";

    data.forEach(s => {
      let li = document.createElement("li");

      let nom = s.properties?.name || "École inconnue";

      li.textContent = "🏫 " + nom;
      li.onclick = () => handleSchoolClick(s);

      ul.appendChild(li);
    });
  }

  // 📍 Popup sur la carte Felt
  function showPopup(name) {
    let iframe = document.getElementById("mapFrame");
    let rect = iframe.getBoundingClientRect();

    let popup = document.getElementById("popup");

    popup.style.display = "block";
    popup.style.left = rect.left + rect.width / 2 + "px";
    popup.style.top = rect.top + rect.height / 2 + "px";

    popup.innerHTML = `🏫 ${name}`;
  }

  // 🎯 Click ou recherche école
  function handleSchoolClick(school) {

    currentSchool = school;

    let [lon, lat] = school.geometry.coordinates;
    let nom = school.properties?.name || "École inconnue";

    // 🗺️ Zoom sur la carte
    document.getElementById("mapFrame").src =
      `https://felt.com/embed/map/Untitled-Map-trd59Cqj4RuKu8WX9Cw2eYCD?loc=${lat},${lon},17z`;

    // ⏳ Attente pour afficher popup
    setTimeout(() => showPopup(nom), 500);

    let categorie = document.getElementById("categorie").value;

    // 🔥 Diagnostic
    fetch(`http://127.0.0.1:8000/diagnostic/recherche/${encodeURIComponent(nom)}?categorie=${categorie}`)
      .then(r => r.json())
      .then(data => afficherResultat(data))
      .catch(() => {
        document.getElementById("result").innerHTML =
          "<p style='color:red'>❌ Erreur diagnostic</p>";
      });

    // 🔥 Simulation
    fetch(`http://127.0.0.1:8000/diagnostic/simulation/${encodeURIComponent(nom)}`)
      .then(r => r.json())
      .then(data => afficherSimulation(data))
      .catch(() => {
        document.getElementById("simulation").innerHTML =
          "<p style='color:red'>❌ Erreur simulation</p>";
      });
  }

  // 📊 RESULTAT + LÉGENDE TEMPÉRATURE
  function afficherResultat(data) {

    let html = `
      <h3>${data.nom}</h3>

      <div class="score ${data.barometre.toLowerCase()}">
        🌡️ ${data.score_alerte} - ${data.barometre}
      </div>

      <!-- 🔥 TEMPÉRATURE EXPLIQUÉE -->
      <p>
        🌡️ <b>${data.alea_argile}</b>
      </p>
      <small style="opacity:0.6;">
        Δ = écart de température par rapport à une zone rurale (îlot de chaleur urbain)
      </small>
    `;

    // 📋 Recommandations
    if (data.recommandation) {
      Object.entries(data.recommandation).forEach(([section, liste]) => {

        html += `<h4>${section}</h4><ul>`;

        liste.forEach(item => {
          html += `<li>${item}</li>`;
        });

        html += "</ul>";
      });
    }

    document.getElementById("result").innerHTML = html;
  }

  // 📊 Simulation
  function afficherSimulation(data) {

    if (!data.simulation) {
      document.getElementById("simulation").innerHTML =
        "<p>❌ Pas de simulation</p>";
      return;
    }

    document.getElementById("simulation").innerHTML = `
      <h3>📊 Simulation</h3>
      <p><b>${data.profil_risque}</b></p>
      <p>🌱 ${data.simulation.surface_renaturee}</p>
      <p>💰 ${data.simulation.investissement_estime}</p>
      <p>💸 ${data.simulation.economie_reparation_evitee}</p>
      <p><b>${data.simulation.bilan_net_20_ans}</b></p>
      <p>${data.conclusion}</p>
    `;
  }

  // 🔍 Recherche
  function searchSchool() {

    let input = normalize(document.getElementById("search").value);

    let found = schoolsData.find(s =>
      normalize(s.properties?.name).includes(input)
    );

    if (found) {
      handleSchoolClick(found);
    } else {
      alert("École non trouvée");
    }
  }

  // 🔘 Bouton
  document.getElementById("btnSearch")
    .addEventListener("click", searchSchool);

  // 🔄 Changement catégorie
  document.getElementById("categorie")
    .addEventListener("change", () => {
      if (currentSchool) handleSchoolClick(currentSchool);
    });

});