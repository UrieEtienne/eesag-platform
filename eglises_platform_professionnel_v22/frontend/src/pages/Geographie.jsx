import { useEffect, useState } from "react";
import client from "../api/client";

export default function Geographie() {
  const [regions, setRegions] = useState([]);
  const [nouvelleRegion, setNouvelleRegion] = useState("");
  const [prefectures, setPrefectures] = useState([]);
  const [formPrefecture, setFormPrefecture] = useState({ nom: "", region: "" });
  const [districts, setDistricts] = useState([]);
  const [formDistrict, setFormDistrict] = useState({ nom: "", prefecture: "" });

  const chargerTout = () => {
    client.get("/geo/regions/").then((r) => setRegions(r.data.results || r.data));
    client.get("/geo/prefectures/").then((r) => setPrefectures(r.data.results || r.data));
    client.get("/geo/districts/").then((r) => setDistricts(r.data.results || r.data));
  };
  useEffect(chargerTout, []);

  const ajouterRegion = async (e) => {
    e.preventDefault();
    if (!nouvelleRegion.trim()) return;
    await client.post("/geo/regions/", { nom: nouvelleRegion });
    setNouvelleRegion("");
    chargerTout();
  };

  const ajouterPrefecture = async (e) => {
    e.preventDefault();
    await client.post("/geo/prefectures/", formPrefecture);
    setFormPrefecture({ nom: "", region: "" });
    chargerTout();
  };

  const ajouterDistrict = async (e) => {
    e.preventDefault();
    await client.post("/geo/districts/", formDistrict);
    setFormDistrict({ nom: "", prefecture: "" });
    chargerTout();
  };

  return (
    <div>
      <div className="barre-superieure"><h2>Découpage géographique</h2></div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 20 }}>
        <div className="carte">
          <h3>Régions</h3>
          <form onSubmit={ajouterRegion} style={{ display: "flex", gap: 8, marginBottom: 12 }}>
            <input placeholder="Nom de la région" value={nouvelleRegion} onChange={(e) => setNouvelleRegion(e.target.value)} />
            <button className="btn btn-petit">+</button>
          </form>
          <ul>{regions.map((r) => <li key={r.id}>{r.nom}</li>)}</ul>
        </div>

        <div className="carte">
          <h3>Préfectures</h3>
          <form onSubmit={ajouterPrefecture} style={{ display: "flex", flexDirection: "column", gap: 8, marginBottom: 12 }}>
            <input placeholder="Nom de la préfecture" value={formPrefecture.nom} onChange={(e) => setFormPrefecture((f) => ({ ...f, nom: e.target.value }))} />
            <select value={formPrefecture.region} onChange={(e) => setFormPrefecture((f) => ({ ...f, region: e.target.value }))}>
              <option value="">-- Région --</option>
              {regions.map((r) => <option key={r.id} value={r.id}>{r.nom}</option>)}
            </select>
            <button className="btn btn-petit">Ajouter</button>
          </form>
          <ul>{prefectures.map((p) => <li key={p.id}>{p.nom} ({p.region_nom})</li>)}</ul>
        </div>

        <div className="carte">
          <h3>Districts</h3>
          <form onSubmit={ajouterDistrict} style={{ display: "flex", flexDirection: "column", gap: 8, marginBottom: 12 }}>
            <input placeholder="Nom du district" value={formDistrict.nom} onChange={(e) => setFormDistrict((f) => ({ ...f, nom: e.target.value }))} />
            <select value={formDistrict.prefecture} onChange={(e) => setFormDistrict((f) => ({ ...f, prefecture: e.target.value }))}>
              <option value="">-- Préfecture --</option>
              {prefectures.map((p) => <option key={p.id} value={p.id}>{p.nom}</option>)}
            </select>
            <button className="btn btn-petit">Ajouter</button>
          </form>
          <ul>{districts.map((d) => <li key={d.id}>{d.nom} ({d.prefecture_nom})</li>)}</ul>
        </div>
      </div>
    </div>
  );
}
