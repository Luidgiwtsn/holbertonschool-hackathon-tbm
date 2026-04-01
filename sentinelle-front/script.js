let schoolsData = [];

// 🔥 Charger GeoJSON
fetch("data/export.geojson")
  .then(res => res.json())
  .then(data => {
    schoolsData = data.features;
    afficherListe(schoolsData);
    console.log("✅ écoles chargées");
  })
  .catch(err => console.error("❌ erreur chargement", err));

// 🔥 Afficher liste
function afficherListe(data) {
  let liste = document.getElementById("listeEcoles");
  liste.innerHTML = "";

  data.forEach(school => {
    if (!school.geometry) return; // 🔥 sécurité

    let li = document.createElement("li");
    let nom = school.properties.name || "École inconnue";

    li.textContent = nom;
    li.onclick = () => handleSchoolClick(school);

    liste.appendChild(li);
  });
}

// 🔥 CLIC école
async function handleSchoolClick(school) {
  let nom = school.properties.name;

  if (!school.geometry) {
    alert("Pas de coordonnées");
    return;
  }

  let [lon, lat] = school.geometry.coordinates;

  // 🗺️ déplacer carte
  document.getElementById("mapFrame").src =
    `https://felt.com/embed/map/Untitled-Map-trd59Cqj4RuKu8WX9Cw2eYCD?loc=${lat},${lon},15z&legend=1`;

  try {
    let res = await fetch(
      `http://127.0.0.1:8000/diagnostic/recherche/${encodeURIComponent(nom)}?categorie=public`
    );

    if (!res.ok) throw new Error("Erreur API");

    let data = await res.json();

    document.getElementById("result").innerHTML = `
      <h3>${data.nom}</h3>
      <p><b>Score :</b> ${data.score_alerte}</p>
      <p><b>Baromètre :</b> ${data.barometre}</p>
      <p><b>Argile :</b> ${data.alea_argile}</p>
      <pre>${data.recommandation}</pre>
    `;

  } catch (err) {
    console.error(err);
    document.getElementById("result").innerHTML =
      "<p style='color:red'>❌ Erreur backend</p>";
  }
}

// 🔍 Recherche
function searchSchool() {
  let input = document.getElementById("search").value.toLowerCase();

  let found = schoolsData.find(s =>
    (s.properties.name || "").toLowerCase().includes(input)
  );

  if (found) {
    handleSchoolClick(found);
  } else {
    alert("École non trouvée");
  }
}
