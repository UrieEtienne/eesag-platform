import { useCallback, useEffect, useMemo, useState } from "react";
import client from "../api/client";
import { useAuth } from "../context/AuthContext";

function extraireListe(data) {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.results)) return data.results;
  return [];
}

export default function Departements() {
  const { utilisateur } = useAuth();

  const [items, setItems] = useState([]);
  const [nom, setNom] = useState("");
  const [recherche, setRecherche] = useState("");
  const [afficherFormulaire, setAfficherFormulaire] = useState(false);
  const [chargement, setChargement] = useState(true);
  const [enregistrement, setEnregistrement] = useState(false);
  const [msg, setMsg] = useState("");
  const [erreur, setErreur] = useState("");

  const charger = useCallback(async () => {
    setChargement(true);
    setErreur("");

    try {
      const response = await client.get("/departements/");
      setItems(extraireListe(response.data));
    } catch (error) {
      setItems([]);
      setErreur(
        error.response?.data?.detail ||
          "Impossible de charger les départements."
      );
    } finally {
      setChargement(false);
    }
  }, []);

  useEffect(() => {
    charger();
  }, [charger]);

  const departementsFiltres = useMemo(() => {
    const terme = recherche.trim().toLocaleLowerCase("fr");

    if (!terme) return items;

    return items.filter((departement) =>
      String(departement.nom || "")
        .toLocaleLowerCase("fr")
        .includes(terme)
    );
  }, [items, recherche]);

  const totalMembres = useMemo(
    () =>
      items.reduce(
        (total, departement) =>
          total + Number(departement.nombre_membres || 0),
        0
      ),
    [items]
  );

  const ajouter = async (e) => {
    e.preventDefault();

    const nomFinal = nom.trim();
    if (!nomFinal) return;

    setErreur("");
    setMsg("");
    setEnregistrement(true);

    try {
      await client.post("/departements/", { nom: nomFinal });

      setNom("");
      setAfficherFormulaire(false);
      setMsg("Le département a été ajouté avec succès.");
      await charger();
    } catch (error) {
      const data = error.response?.data;
      setErreur(
        data?.detail ||
          data?.nom?.[0] ||
          JSON.stringify(data || {}) ||
          "Impossible d'ajouter le département."
      );
    } finally {
      setEnregistrement(false);
    }
  };

  return (
    <div className="page-departements">
      <style>{`
        .page-departements {
          color: var(--text-primary, #243047);
          width: 100%;
        }
        .dep-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 20px;
          flex-wrap: wrap;
          margin-bottom: 24px;
        }
        .dep-eyebrow {
          color: #b58a35;
          font-size: 11px;
          font-weight: 800;
          letter-spacing: 1.5px;
        }
        .dep-header h1 {
          margin: 7px 0;
          font-size: clamp(25px, 4vw, 34px);
          font-weight: 800;
        }
        .dep-description {
          color: var(--text-secondary, #718096);
          margin: 0;
          line-height: 1.6;
        }
        .dep-button {
          border: 0;
          border-radius: 10px;
          background: #b58a35;
          color: #fff;
          padding: 12px 18px;
          font-weight: 700;
          cursor: pointer;
        }
        .dep-button:hover { background: #987027; }
        .dep-button:disabled { opacity: .6; cursor: wait; }
        .dep-stats {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 16px;
          margin-bottom: 22px;
        }
        .dep-stat, .dep-panel {
          background: var(--card-bg, #fff);
          border: 1px solid var(--border-color, #e6eaf0);
          border-radius: 14px;
          padding: 20px;
          box-shadow: 0 3px 12px rgba(25, 35, 50, .04);
        }
        .dep-stat-label {
          color: var(--text-secondary, #718096);
          font-size: 13px;
          font-weight: 600;
        }
        .dep-stat-value {
          display: block;
          margin-top: 8px;
          font-size: 29px;
          font-weight: 800;
          color: var(--text-primary, #243047);
        }
        .dep-panel { margin-bottom: 18px; }
        .dep-panel-heading {
          display: flex;
          justify-content: space-between;
          align-items: center;
          flex-wrap: wrap;
          gap: 12px;
          margin-bottom: 16px;
        }
        .dep-panel-heading h2 {
          margin: 0;
          font-size: 18px;
          font-weight: 750;
        }
        .dep-search {
          width: min(100%, 340px);
          padding: 11px 13px;
          border: 1px solid var(--border-color, #dce2ea);
          border-radius: 9px;
          background: var(--input-bg, #fff);
          color: var(--text-primary, #243047);
          outline: none;
        }
        .dep-search:focus {
          border-color: #b58a35;
          box-shadow: 0 0 0 3px rgba(181, 138, 53, .12);
        }
        .dep-table-wrap { width: 100%; overflow-x: auto; }
        .dep-table {
          width: 100%;
          border-collapse: collapse;
          min-width: 480px;
        }
        .dep-table th {
          background: var(--table-header-bg, #f6f7f9);
          color: var(--text-secondary, #68758a);
          font-size: 11px;
          text-transform: uppercase;
          letter-spacing: .6px;
          text-align: left;
          padding: 14px;
        }
        .dep-table td {
          padding: 15px 14px;
          border-bottom: 1px solid var(--border-color, #edf0f4);
          color: var(--text-primary, #243047);
        }
        .dep-table tbody tr:hover {
          background: var(--table-hover-bg, #faf8f2);
        }
        .dep-number {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          min-width: 30px;
          height: 30px;
          border-radius: 8px;
          background: rgba(181, 138, 53, .12);
          color: #9a7228;
          font-weight: 800;
        }
        .dep-count {
          font-weight: 750;
          font-variant-numeric: tabular-nums;
        }
        .dep-message {
          padding: 12px 15px;
          border-radius: 9px;
          margin-bottom: 16px;
        }
        .dep-success {
          background: #eaf7ef;
          color: #17683b;
          border: 1px solid #c9ead5;
        }
        .dep-error {
          background: #fff0f0;
          color: #a52b2b;
          border: 1px solid #f2cccc;
          overflow-wrap: anywhere;
        }
        .dep-empty {
          padding: 35px 15px;
          text-align: center;
          color: var(--text-secondary, #718096);
        }
        .dep-form {
          display: grid;
          grid-template-columns: minmax(0, 1fr) auto;
          gap: 12px;
          align-items: end;
          margin-bottom: 20px;
        }
        .dep-form label {
          display: block;
          font-size: 13px;
          font-weight: 700;
          margin-bottom: 7px;
        }
        .dep-form input {
          width: 100%;
          box-sizing: border-box;
          padding: 12px;
          border: 1px solid var(--border-color, #dce2ea);
          border-radius: 9px;
          background: var(--input-bg, #fff);
          color: var(--text-primary, #243047);
        }
        .dep-form input:focus {
          outline: 2px solid rgba(181, 138, 53, .2);
          border-color: #b58a35;
        }
        .dep-cancel {
          background: transparent;
          color: var(--text-secondary, #718096);
          border: 1px solid var(--border-color, #dce2ea);
          border-radius: 9px;
          padding: 11px 15px;
          cursor: pointer;
        }
        .dep-church {
          color: var(--text-secondary, #718096);
          font-size: 13px;
          margin-top: 18px;
        }
        @media (max-width: 600px) {
          .dep-stats { grid-template-columns: 1fr 1fr; gap: 10px; }
          .dep-stat, .dep-panel { padding: 14px; }
          .dep-stat-value { font-size: 24px; }
          .dep-form { grid-template-columns: 1fr; }
          .dep-form-actions { display: flex; gap: 8px; }
        }
      `}</style>

      <header className="dep-header">
        <div>
          <span className="dep-eyebrow">ORGANISATION DE L’ÉGLISE LOCALE</span>
          <h1>Départements</h1>
          <p className="dep-description">
            Gérez les départements et consultez leur nombre de membres.
          </p>
        </div>

        <button
          type="button"
          className="dep-button"
          onClick={() => {
            setAfficherFormulaire((visible) => !visible);
            setMsg("");
            setErreur("");
          }}
        >
          {afficherFormulaire ? "Fermer le formulaire" : "＋ Ajouter un département"}
        </button>
      </header>

      {msg && <div className="dep-message dep-success">{msg}</div>}
      {erreur && <div className="dep-message dep-error">{erreur}</div>}

      <section className="dep-stats">
        <div className="dep-stat">
          <span className="dep-stat-label">Départements enregistrés</span>
          <strong className="dep-stat-value">{items.length}</strong>
        </div>
        <div className="dep-stat">
          <span className="dep-stat-label">Membres répartis</span>
          <strong className="dep-stat-value">{totalMembres}</strong>
        </div>
      </section>

      {afficherFormulaire && (
        <section className="dep-panel">
          <div className="dep-panel-heading">
            <h2>Nouveau département</h2>
          </div>

          <form className="dep-form" onSubmit={ajouter}>
            <div>
              <label htmlFor="nom-departement">Nom du département</label>
              <input
                id="nom-departement"
                value={nom}
                onChange={(e) => setNom(e.target.value)}
                placeholder="Ex. Jeunesse, Femmes, Hommes…"
                maxLength={150}
                required
                autoFocus
              />
            </div>

            <div className="dep-form-actions">
              <button
                type="submit"
                className="dep-button"
                disabled={enregistrement || !nom.trim()}
              >
                {enregistrement ? "Enregistrement…" : "Enregistrer"}
              </button>
              <button
                type="button"
                className="dep-cancel"
                onClick={() => {
                  setAfficherFormulaire(false);
                  setNom("");
                }}
              >
                Annuler
              </button>
            </div>
          </form>
        </section>
      )}

      <section className="dep-panel">
        <div className="dep-panel-heading">
          <h2>Liste des départements</h2>
          <input
            className="dep-search"
            type="search"
            placeholder="Rechercher un département…"
            value={recherche}
            onChange={(e) => setRecherche(e.target.value)}
            aria-label="Rechercher un département"
          />
        </div>

        <div className="dep-table-wrap">
          <table className="dep-table">
            <thead>
              <tr>
                <th>N°</th>
                <th>Nom du département</th>
                <th>Membres</th>
              </tr>
            </thead>
            <tbody>
              {departementsFiltres.map((departement, index) => (
                <tr key={departement.id}>
                  <td><span className="dep-number">{index + 1}</span></td>
                  <td><strong>{departement.nom}</strong></td>
                  <td>
                    <span className="dep-count">
                      {departement.nombre_membres ?? 0}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {chargement && (
          <div className="dep-empty">Chargement des départements…</div>
        )}

        {!chargement && !departementsFiltres.length && (
          <div className="dep-empty">
            {recherche
              ? "Aucun département ne correspond à votre recherche."
              : "Aucun département enregistré pour le moment."}
          </div>
        )}
      </section>

      <p className="dep-church">
        Église connectée :{" "}
        <strong>{utilisateur?.eglise_nom || "votre église"}</strong>
      </p>
    </div>
  );
}