import { useCallback, useEffect, useMemo, useState } from "react";
import "../styles/AdministrationGlobale.css";

const API_URL = (import.meta.env.VITE_API_URL || "/api").replace(/\/+$/, "");

function obtenirToken() {
  return (
    localStorage.getItem("access") ||
    localStorage.getItem("access_token") ||
    localStorage.getItem("accessToken") ||
    localStorage.getItem("token") ||
    ""
  );
}

async function requeteAPI(chemin, options = {}) {
  const token = obtenirToken();

  const response = await fetch(`${API_URL}${chemin}`, {
    ...options,
    headers: {
      Accept: "application/json",
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });

  const type = response.headers.get("content-type") || "";
  const data = type.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const detail =
      typeof data === "string"
        ? data
        : data?.detail ||
          data?.message ||
          `Erreur HTTP ${response.status}`;
    throw new Error(detail);
  }

  return data;
}

function listeDepuis(data) {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.results)) return data.results;
  if (Array.isArray(data?.data)) return data.data;
  return [];
}

function badgeStatut(statut) {
  const valeur = String(statut || "").toUpperCase();

  if (valeur === "ACTIVE" || valeur === "ACTIF") {
    return <span className="ag-badge ag-badge-green">Active</span>;
  }
  if (valeur === "SUSPENDUE" || valeur === "SUSPENDU") {
    return <span className="ag-badge ag-badge-orange">Suspendue</span>;
  }
  if (valeur === "FERMEE" || valeur === "FERMÉE") {
    return <span className="ag-badge ag-badge-red">Fermée</span>;
  }

  return <span className="ag-badge ag-badge-gray">{statut || "Non renseigné"}</span>;
}

export default function AdministrationEglises() {
  const [eglises, setEglises] = useState([]);
  const [chargement, setChargement] = useState(true);
  const [actionEnCours, setActionEnCours] = useState(null);
  const [recherche, setRecherche] = useState("");
  const [filtrePlateforme, setFiltrePlateforme] = useState("TOUTES");
  const [filtreStatut, setFiltreStatut] = useState("TOUS");
  const [message, setMessage] = useState("");
  const [erreur, setErreur] = useState("");

  const chargerEglises = useCallback(async () => {
    setChargement(true);
    setErreur("");

    try {
      const data = await requeteAPI("/eglises/");
      setEglises(listeDepuis(data));
    } catch (e) {
      setErreur(e.message || "Impossible de charger les églises.");
    } finally {
      setChargement(false);
    }
  }, []);

  useEffect(() => {
    chargerEglises();
  }, [chargerEglises]);

  const changerPlateforme = async (eglise) => {
    if (!eglise?.id) {
      setErreur("Identifiant de l'église introuvable.");
      return;
    }

    const activer = !eglise.plateforme_active;
    const action = activer ? "activer_plateforme" : "desactiver_plateforme";

    if (
      !window.confirm(
        `Confirmer la ${activer ? "mise en service" : "désactivation"} de la plateforme de « ${eglise.nom} » ?`
      )
    ) return;

    setActionEnCours(eglise.id);
    setErreur("");
    setMessage("");

    try {
      const resultat = await requeteAPI(
        `/eglises/${eglise.id}/${action}/`,
        { method: "POST" }
      );

      setMessage(
        resultat?.detail ||
          `La plateforme de ${eglise.nom} a été ${activer ? "activée" : "désactivée"}.`
      );

      await chargerEglises();
    } catch (e) {
      setErreur(e.message || "Impossible de modifier la plateforme.");
    } finally {
      setActionEnCours(null);
    }
  };

  const eglisesFiltrees = useMemo(() => {
    const terme = recherche.trim().toLocaleLowerCase();

    return eglises.filter((eglise) => {
      const correspondRecherche =
        !terme ||
        [
          eglise.nom,
          eglise.code,
          eglise.region_nom,
          eglise.prefecture_nom,
          eglise.district_nom,
          eglise.commune_nom,
          eglise.telephone,
          eglise.statut,
        ]
          .filter(Boolean)
          .some((v) => String(v).toLocaleLowerCase().includes(terme));

      const correspondPlateforme =
        filtrePlateforme === "TOUTES" ||
        (filtrePlateforme === "ACTIVE" && eglise.plateforme_active) ||
        (filtrePlateforme === "INACTIVE" && !eglise.plateforme_active);

      const statut = String(eglise.statut || "").toUpperCase();
      const correspondStatut =
        filtreStatut === "TOUS" ||
        statut === filtreStatut;

      return correspondRecherche && correspondPlateforme && correspondStatut;
    });
  }, [eglises, recherche, filtrePlateforme, filtreStatut]);

  const plateformesActives = eglises.filter((e) => e.plateforme_active).length;
  const plateformesInactives = eglises.length - plateformesActives;
  const eglisesSuspendues = eglises.filter(
    (e) => String(e.statut).toUpperCase() === "SUSPENDUE"
  ).length;

  return (
    <main className="admin-global">
      <header className="ag-heading">
        <div>
          <div className="ag-eyebrow">EESAG · Contrôle global</div>
          <h2>Gestion des églises</h2>
          <p>Annuaire national et contrôle des accès aux plateformes locales.</p>
        </div>

        <button
          type="button"
          className="btn btn-outline-secondary btn-sm"
          onClick={chargerEglises}
          disabled={chargement}
        >
          {chargement ? "Chargement..." : "↻ Actualiser"}
        </button>
      </header>

      {erreur && <div className="alert alert-danger ag-alert">{erreur}</div>}
      {message && <div className="alert alert-success ag-alert">{message}</div>}

      <section className="ag-stats">
        <div className="ag-stat ag-blue">
          <span className="ag-stat-label">Églises enregistrées</span>
          <span className="ag-stat-value">{eglises.length}</span>
        </div>
        <div className="ag-stat ag-green">
          <span className="ag-stat-label">Plateformes activées</span>
          <span className="ag-stat-value">{plateformesActives}</span>
        </div>
        <div className="ag-stat ag-red">
          <span className="ag-stat-label">Plateformes désactivées</span>
          <span className="ag-stat-value">{plateformesInactives}</span>
        </div>
        <div className="ag-stat ag-orange">
          <span className="ag-stat-label">Églises suspendues</span>
          <span className="ag-stat-value">{eglisesSuspendues}</span>
        </div>
      </section>

      <section className="ag-panel">
        <div className="ag-toolbar">
          <h5>Annuaire de toutes les églises</h5>

          <div className="ag-filters">
            <input
              type="search"
              className="ag-control ag-search"
              placeholder="Rechercher une église, un code, une région..."
              value={recherche}
              onChange={(e) => setRecherche(e.target.value)}
              aria-label="Rechercher une église"
            />

            <select
              className="ag-control"
              value={filtrePlateforme}
              onChange={(e) => setFiltrePlateforme(e.target.value)}
              aria-label="Filtrer par plateforme"
            >
              <option value="TOUTES">Toutes les plateformes</option>
              <option value="ACTIVE">Plateformes activées</option>
              <option value="INACTIVE">Plateformes désactivées</option>
            </select>

            <select
              className="ag-control"
              value={filtreStatut}
              onChange={(e) => setFiltreStatut(e.target.value)}
              aria-label="Filtrer par statut administratif"
            >
              <option value="TOUS">Tous les statuts</option>
              <option value="ACTIVE">Active</option>
              <option value="SUSPENDUE">Suspendue</option>
              <option value="FERMEE">Fermée</option>
            </select>
          </div>
        </div>

        {chargement ? (
          <div className="ag-empty">Chargement des églises...</div>
        ) : eglisesFiltrees.length === 0 ? (
          <div className="ag-empty">Aucune église ne correspond aux filtres.</div>
        ) : (
          <div className="ag-table-wrap">
            <table className="ag-table">
              <thead>
                <tr>
                  <th>Église</th>
                  <th>Code</th>
                  <th>Localisation</th>
                  <th>Statut administratif</th>
                  <th>Plateforme EESAG</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {eglisesFiltrees.map((eglise) => (
                  <tr key={eglise.id}>
                    <td>
                      <span className="ag-primary-text">
                        {eglise.nom || "Église sans nom"}
                      </span>
                      <span className="ag-secondary-text">
                        {eglise.telephone || "Téléphone non renseigné"}
                      </span>
                    </td>
                    <td>{eglise.code || "—"}</td>
                    <td>
                      {[
                        eglise.commune_nom,
                        eglise.district_nom,
                        eglise.prefecture_nom,
                        eglise.region_nom,
                      ].filter(Boolean).join(" · ") || "—"}
                    </td>
                    <td>{badgeStatut(eglise.statut)}</td>
                    <td>
                      {eglise.plateforme_active ? (
                        <span className="ag-badge ag-badge-green">Activée</span>
                      ) : (
                        <span className="ag-badge ag-badge-red">Désactivée</span>
                      )}
                    </td>
                    <td>
                      <button
                        type="button"
                        className={`ag-action ${eglise.plateforme_active ? "ag-action-red" : "ag-action-green"}`}
                        disabled={actionEnCours === eglise.id}
                        onClick={() => changerPlateforme(eglise)}
                      >
                        {actionEnCours === eglise.id
                          ? "Traitement..."
                          : eglise.plateforme_active
                            ? "Désactiver"
                            : "Activer la plateforme"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <footer className="ag-footer">
          {eglisesFiltrees.length} résultat(s) affiché(s) sur {eglises.length} église(s).
          {" "}La création et la modification des églises restent gérées dans Django Admin.
        </footer>
      </section>
    </main>
  );
}
