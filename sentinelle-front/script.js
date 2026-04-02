let schoolsData = [];
let map;
let markers = [];
let currentSchool = null;
let selectedMarker = null;

// 🎓 icône normale
let schoolIcon = L.icon({
  iconUrl: "https://cdn-icons-png.flaticon.com/512/167/167707.png",
  iconSize: [25, 25],
  iconAnchor: [12, 25]
});

// 🔥 icône sélection
let selectedIcon = L.icon({
  iconUrl: "https://cdn-icons-png.flaticon.com/512/684/684908.png",
  iconSize: [35, 35],
  iconAnchor: [17, 35]
});

// 🔤 normalisation
function normalize(text) {
  return text.toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

// 🗺️ INIT
function initMap() {
  map = L.map('map').setView([44.84, -0.58], 12);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap'
  }).addTo(map);
}

// 📦 CHARGEMENT
fetch("data/export.geojson")
  .then(r => r.json())
  .then(data => {
    schoolsData = data.features;
    afficherListe(schoolsData);
    afficherPoints(schoolsData);
  });

// 📍 markers normaux
function afficherPoints(data) {
  data.forEach(s => {
    if (!s.geometry) return;

    let [lon, lat] = s.geometry.coordinates;

    let marker = L.marker([lat, lon], { icon: schoolIcon }).addTo(map);

    marker.bindPopup("🏫 " + s.properties.name);

    marker.on("click", () => handleSchoolClick(s));

    markers.push(marker);
  });
}

// 📋 liste
function afficherListe(data) {
  let ul = document.getElementById("listeEcoles");
  ul.innerHTML = "";

  data.forEach(s => {
    let li = document.createElement("li");
    li.textContent = "🏫 " + s.properties.name;
    li.onclick = () => handleSchoolClick(s);
    ul.appendChild(li);
  });
}

// 🎯 CLICK / RECHERCHE
function handleSchoolClick(school) {
  currentSchool = school;

  let [lon, lat] = school.geometry.coordinates;

  map.setView([lat, lon], 16);

  // ❌ enlever ancien marker
  if (selectedMarker) {
    map.removeLayer(selectedMarker);
  }

  // ✅ nouveau marker + popup auto
  selectedMarker = L.marker([lat, lon], { icon: selectedIcon })
    .addTo(map)
    .bindPopup("🏫 " + school.properties.name)
    .openPopup();   // 🔥 ICI LA MAGIE

  let nom = school.properties.name;
  let categorie = document.getElementById("categorie").value;

  fetch(`http://127.0.0.1:8000/diagnostic/recherche/${encodeURIComponent(nom)}?categorie=${categorie}`)
    .then(r => r.json())
    .then(data => afficherResultat(data));
}

// 🔄 catégorie
document.getElementById("categorie").addEventListener("change", () => {
  if (currentSchool) handleSchoolClick(currentSchool);
});

// 📊 RESULTAT
function afficherResultat(data) {
  let couleur = data.barometre.toLowerCase();

  document.getElementById("result").innerHTML = `
    <div class="score ${couleur}">
      <h3>${data.nom}</h3>
      <p>Score : ${data.score_alerte}</p>
      <p>${data.barometre}</p>
      <p>Argile : ${data.alea_argile}</p>
    </div>

    <div class="reco">
      ${data.recommandation.replace(/\n/g, "<br>")}
    </div>
  `;
}

// 🔍 RECHERCHE
function searchSchool() {
  let input = normalize(document.getElementById("search").value);

  let found = schoolsData.find(s =>
    normalize(s.properties.name).includes(input)
  );

  if (found) handleSchoolClick(found);
  else alert("École non trouvée");
}

// 🚀 INIT
initMap();