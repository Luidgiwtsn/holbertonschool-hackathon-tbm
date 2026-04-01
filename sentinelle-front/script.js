let schoolsData = [];

// Charger GeoJSON
fetch("data/export.geojson")
  .then(res => res.json())
  .then(data => {
    schoolsData = data.features;
    afficherListe(schoolsData);
  });


// Liste écoles
function afficherListe(data) {
  let liste = document.getElementById("listeEcoles");

  data.forEach(school => {
    let li = document.createElement("li");
    li.textContent = school.properties.name;

    li.onclick = () => handleSchoolClick(school);

    liste.appendChild(li);
  });
}


// 🔥 ACTION PRINCIPALE
async function handleSchoolClick(school) {
  let coords = school.geometry.coordinates;
  let lon = coords[0];
  let lat = coords[1];
  let nom = school.properties.name;

  // 🗺️ déplacer carte
  document.getElementById("mapFrame").src =
    `https://felt.com/embed/map/Untitled-Map-trd59Cqj4RuKu8WX9Cw2eYCD?loc=${lat},${lon},15z&legend=1`;

  // 🔥 appeler backend
  try {
    let res = await fetch(
      `http://127.0.0.1:8000/diagnostic/recherche/${encodeURIComponent(nom)}?categorie=public`
    );

    let data = await res.json();

    document.getElementById("result").innerHTML = `
      <h3>${data.nom}</h3>
      <p>Score : ${data.score_alerte}</p>
      <p>Niveau : ${data.barometre}</p>
      <p>Argile : ${data.alea_argile}</p>
      <pre>${data.recommandation}</pre>
    `;

  } catch {
    document.getElementById("result").innerHTML =
      "❌ Erreur connexion API";
  }
}


// Recherche
function searchSchool() {
  let input = document.getElementById("search").value.toLowerCase();

  let school = schoolsData.find(s =>
    s.properties.name.toLowerCase().includes(input)
  );

  if (school) handleSchoolClick(school);
  else alert("École non trouvée");
}
