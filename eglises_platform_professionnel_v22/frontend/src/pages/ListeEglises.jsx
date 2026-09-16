import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import client from "../api/client";
import { useAuth } from "../context/AuthContext";
import FormulaireEglise from "../components/FormulaireEglise";

export default function ListeEglises() {
  const [eglises, setEglises] = useState([]);
  const [religions, setReligions] = useState([]);
  const [recherche, setRecherche] = useState("");
  const [religionFiltre, setReligionFiltre] = useState("");
  const [afficherFormulaire, setAfficherFormulaire] = useState(false);
  const { estNational, utilisateur } = useAuth();

  const charger = () => {
    const params = {};
    if (recherche) params.search = recherche;
    if (religionFiltre) params.religion = religionFiltre;
    client.get("/eglises/", { params }).then((res) => setEglises(res.data.results || res.data));
  };

  useEffect(() => {
    client.get("/religions/").then((res) => setReligions(res.data.results || res.data));
  }, []);

  useEffect(() => {
    const delai = setTimeout(charger, 300);
    return () => clearTimeout(delai);
  }, [recherche, religionFiltre]);

  return (
    <div>
      <div className="barre-superieure">
        <div><h2>Annuaire des églises</h2><p className="sous-titre">Recherche nationale des établissements. Le contenu interne reste privé.</p></div>
        {estNational && (
          <button className="btn" onClick={() => setAfficherFormulaire(true)}>+ Créer une église</button>
        )}
      </div>

      <div className="filtres">
        <input
          placeholder="Rechercher une église (nom, code, adresse)..."
          value={recherche}
          onChange={(e) => setRecherche(e.target.value)}
          style={{ minWidth: 280 }}
        />
        <select value={religionFiltre} onChange={(e) => setReligionFiltre(e.target.value)}>
          <option value="">Toutes les religions</option>
          {religions.map((r) => <option key={r.id} value={r.id}>{r.nom}</option>)}
        </select>
      </div>

      <div className="carte table-wrap">
        <table>
          <thead><tr>
            <th>Code</th><th>Église</th><th>Religion</th><th>Région</th><th>Préfecture</th>
            {estNational && <><th>Responsable</th><th>Membres</th></>}
            <th>Statut</th><th></th>
          </tr></thead>
          <tbody>
            {eglises.map((e) => (
              <tr key={e.id}>
                <td><b>{e.code}</b></td><td>{e.nom}</td><td>{e.religion_nom}</td><td>{e.region_nom}</td><td>{e.prefecture_nom}</td>
                {estNational && <><td>{e.responsable_nom || "— non affecté —"}</td><td>{e.nombre_membres}</td></>}
                <td><span className="tag">{e.statut}</span></td>
                <td>{(estNational || utilisateur?.eglise === e.id) ? <Link className="btn btn-petit btn-secondaire" to={`/eglises/${e.id}`}>Ouvrir</Link> : <span className="tag">Annuaire</span>}</td>
              </tr>
            ))}
            {eglises.length === 0 && <tr><td colSpan={estNational ? 9 : 7}><div className="empty-state">Aucune église trouvée.</div></td></tr>}
          </tbody>
        </table>
      </div>

      {afficherFormulaire && (
        <FormulaireEglise
          onFerme={() => setAfficherFormulaire(false)}
          onCree={() => { setAfficherFormulaire(false); charger(); }}
        />
      )}
    </div>
  );
}
