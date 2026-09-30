import { useCallback, useEffect, useState } from "react";
import client from "../api/client";
import { useAuth } from "../context/AuthContext";

const formulaireVide = { nom: "", adresse: "", telephone: "", date_creation: "" };

function liste(data) {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.results)) return data.results;
  return [];
}

export default function Annexes() {
  const { utilisateur, estGestionnaireEglise } = useAuth();
  const [annexes, setAnnexes] = useState([]);
  const [afficher, setAfficher] = useState(false);
  const [editionId, setEditionId] = useState(null);
  const [form, setForm] = useState(formulaireVide);
  const [erreur, setErreur] = useState("");
  const [msg, setMsg] = useState("");
  const [chargement, setChargement] = useState(true);

  const peutGerer = Boolean(estGestionnaireEglise && utilisateur?.eglise);

  const charger = useCallback(async () => {
    setChargement(true);
    setErreur("");
    try {
      const response = await client.get("/annexes/");
      setAnnexes(liste(response.data));
    } catch (error) {
      setAnnexes([]);
      setErreur(
        error.response?.data?.detail ||
        "Impossible de charger les annexes de cette église."
      );
    } finally {
      setChargement(false);
    }
  }, []);

  useEffect(() => {
    charger();
  }, [charger]);

  const ouvrirCreation = () => {
    setEditionId(null);
    setForm(formulaireVide);
    setErreur("");
    setMsg("");
    setAfficher(true);
  };

  const ouvrirEdition = (annexe) => {
    setEditionId(annexe.id);
    setForm({
      nom: annexe.nom || "",
      adresse: annexe.adresse || "",
      telephone: annexe.telephone || "",
      date_creation: annexe.date_creation || "",
    });
    setErreur("");
    setMsg("");
    setAfficher(true);
  };

  const fermer = () => {
    setAfficher(false);
    setEditionId(null);
    setForm(formulaireVide);
  };

  const soumettre = async (event) => {
    event.preventDefault();
    if (!peutGerer) return;

    setErreur("");
    setMsg("");
    try {
      if (editionId) {
        await client.patch(`/annexes/${editionId}/`, form);
        setMsg("Annexe modifiée avec succès.");
      } else {
        await client.post("/annexes/", form);
        setMsg("Annexe créée avec succès.");
      }
      fermer();
      await charger();
    } catch (error) {
      setErreur(
        error.response?.data?.detail ||
        "Impossible d'enregistrer cette annexe."
      );
    }
  };

  const supprimer = async (annexe) => {
    if (!peutGerer) return;
    if (!window.confirm(`Supprimer l'annexe « ${annexe.nom} » ?`)) return;

    setErreur("");
    setMsg("");
    try {
      await client.delete(`/annexes/${annexe.id}/`);
      setMsg("Annexe supprimée.");
      await charger();
    } catch (error) {
      setErreur(
        error.response?.data?.detail ||
        "Impossible de supprimer cette annexe."
      );
    }
  };

  return (
    <div>
      <div className="barre-superieure">
        <div>
          <span className="eyebrow">IMPLANTATIONS LOCALES</span>
          <h2>Annexes</h2>
          <p className="sous-titre">
            Gérez les annexes et implantations rattachées exclusivement à votre église.
          </p>
        </div>
        {peutGerer && (
          <button className="btn" onClick={ouvrirCreation}>
            ＋ Nouvelle annexe
          </button>
        )}
      </div>

      {msg && <div className="console-success">{msg}</div>}
      {erreur && <div className="console-error">{erreur}</div>}

      <div className="cards-list">
        {annexes.map((annexe) => (
          <article className="carte card-compact" key={annexe.id}>
            <div className="code-pill">{annexe.code || "ANNEXE"}</div>
            <h3>{annexe.nom}</h3>
            <p>{annexe.adresse || "Adresse non renseignée"}</p>
            <small>{annexe.telephone || "Téléphone non renseigné"}</small>
            <div className="card-footer">
              <span className={annexe.active ? "status-active" : "status-off"}>
                {annexe.active ? "Active" : "Inactive"}
              </span>
              <span>{annexe.responsable_nom || "Sans responsable"}</span>
            </div>
            {peutGerer && (
              <div className="actions" style={{ marginTop: 12 }}>
                <button
                  type="button"
                  className="btn btn-secondaire"
                  onClick={() => ouvrirEdition(annexe)}
                >
                  Modifier
                </button>
                <button
                  type="button"
                  className="btn btn-secondaire"
                  onClick={() => supprimer(annexe)}
                >
                  Supprimer
                </button>
              </div>
            )}
          </article>
        ))}

        {chargement && (
          <div className="carte">
            <div className="empty-state">Chargement des annexes…</div>
          </div>
        )}

        {!chargement && !annexes.length && !erreur && (
          <div className="carte">
            <div className="empty-state">Aucune annexe enregistrée.</div>
          </div>
        )}
      </div>

      <p className="sous-titre">
        Église : <b>{utilisateur?.eglise_nom || "votre église"}</b>
      </p>

      {afficher && (
        <div className="modale-fond" onClick={fermer}>
          <div className="modale" onClick={(e) => e.stopPropagation()}>
            <h3>{editionId ? "Modifier l’annexe" : "Nouvelle annexe"}</h3>
            <form onSubmit={soumettre}>
              <div className="form-champ">
                <label>Nom *</label>
                <input
                  required
                  value={form.nom}
                  onChange={(e) => setForm({ ...form, nom: e.target.value })}
                />
              </div>
              <div className="form-champ">
                <label>Adresse</label>
                <input
                  value={form.adresse}
                  onChange={(e) => setForm({ ...form, adresse: e.target.value })}
                />
              </div>
              <div className="form-champ">
                <label>Téléphone</label>
                <input
                  value={form.telephone}
                  onChange={(e) => setForm({ ...form, telephone: e.target.value })}
                />
              </div>
              <div className="form-champ">
                <label>Date de création</label>
                <input
                  type="date"
                  value={form.date_creation || ""}
                  onChange={(e) => setForm({ ...form, date_creation: e.target.value })}
                />
              </div>
              {erreur && <p className="erreur">{erreur}</p>}
              <div className="modal-actions">
                <button className="btn" type="submit">
                  {editionId ? "Enregistrer" : "Créer l’annexe"}
                </button>
                <button type="button" className="btn btn-secondaire" onClick={fermer}>
                  Annuler
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
