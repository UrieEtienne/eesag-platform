import { useEffect, useState } from "react";
import client from "../api/client";

export default function FormulaireAffectationPasteur({ egliseId, onFerme, onAffecte }) {
  const [terme, setTerme] = useState("");
  const [resultats, setResultats] = useState([]);
  const [selectionne, setSelectionne] = useState(null);
  const [erreur, setErreur] = useState("");

  useEffect(() => {
    if (terme.length < 2) { setResultats([]); return; }
    const delai = setTimeout(() => {
      client.get("/membres/recherche/", { params: { q: terme } }).then((res) => setResultats(res.data));
    }, 300);
    return () => clearTimeout(delai);
  }, [terme]);

  const confirmer = async () => {
    setErreur("");
    try {
      await client.post(`/eglises/${egliseId}/affecter_pasteur/`, { utilisateur_id: selectionne.id });
      onAffecte();
    } catch (err) {
      setErreur("Erreur lors de l'affectation.");
    }
  };

  return (
    <div className="modale-fond" onClick={onFerme}>
      <div className="modale" onClick={(e) => e.stopPropagation()}>
        <h3>Affecter un pasteur</h3>
        <div className="form-champ">
          <label>Rechercher par identifiant ou nom</label>
          <input value={terme} onChange={(e) => setTerme(e.target.value)} placeholder="Ex: Jean Kouyaté ou EGL..." />
        </div>
        <div style={{ maxHeight: 200, overflowY: "auto" }}>
          {resultats.map((r) => (
            <div
              key={r.id}
              onClick={() => setSelectionne(r)}
              style={{
                padding: 8, cursor: "pointer", borderRadius: 6,
                background: selectionne?.id === r.id ? "#eef2f6" : "white",
              }}
            >
              {r.nom_complet} — {r.identifiant} ({r.eglise_nom || "sans église"})
            </div>
          ))}
        </div>
        {selectionne && <p style={{ fontSize: 13 }}>Sélectionné : <b>{selectionne.nom_complet}</b></p>}
        {erreur && <p className="erreur">{erreur}</p>}
        <div style={{ display: "flex", gap: 10, marginTop: 10 }}>
          <button className="btn" disabled={!selectionne} onClick={confirmer}>Confirmer l'affectation</button>
          <button className="btn btn-secondaire" onClick={onFerme}>Annuler</button>
        </div>
      </div>
    </div>
  );
}
