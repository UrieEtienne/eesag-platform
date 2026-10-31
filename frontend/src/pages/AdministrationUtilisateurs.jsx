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
          Object.entries(data || {})
            .map(([champ, valeur]) => {
              const texte = Array.isArray(valeur)
                ? valeur.join(" ")
                : typeof valeur === "string"
                  ? valeur
                  : JSON.stringify(valeur);
              return `${champ}: ${texte}`;
            })
            .join(" | ") ||
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

function nomUtilisateur(u) {
  return [u?.prenom, u?.nom].filter(Boolean).join(" ").trim() ||
    u?.identifiant ||
    "Utilisateur";
}

function libelleRole(u) {
  return u?.role_libelle || u?.role_display || u?.role || "—";
}

function badgeRole(role) {
  const valeur = String(role || "").toUpperCase();

  if (valeur === "COORDINATEUR") {
    return <span className="ag-badge ag-badge-purple ag-badge-blue">Coordinateur</span>;
  }
  if (valeur.includes("SUPERADMIN")) {
    return <span className="ag-badge ag-badge-blue">{libelleRole({ role })}</span>;
  }
  if (valeur === "ADMIN_LOCAL") {
    return <span className="ag-badge ag-badge-orange">Administrateur local</span>;
  }
  if (valeur === "PASTEUR") {
    return <span className="ag-badge ag-badge-green">Pasteur</span>;
  }

  return <span className="ag-badge ag-badge-gray">{role || "—"}</span>;
}

export default function AdministrationUtilisateurs() {
  const [utilisateurs, setUtilisateurs] = useState([]);
  const [chargement, setChargement] = useState(true);
  const [recherche, setRecherche] = useState("");
  const [filtreRole, setFiltreRole] = useState("TOUS");
  const [filtreEtat, setFiltreEtat] = useState("TOUS");
  const [actionEnCours, setActionEnCours] = useState(null);
  const [message, setMessage] = useState("");
  const [erreur, setErreur] = useState("");

  const chargerUtilisateurs = useCallback(async () => {
    setChargement(true);
    setErreur("");

    try {
      const data = await requeteAPI("/utilisateurs/");
      setUtilisateurs(listeDepuis(data));
    } catch (e) {
      setErreur(e.message || "Impossible de charger les utilisateurs.");
    } finally {
      setChargement(false);
    }
  }, []);

  useEffect(() => {
    chargerUtilisateurs();
  }, [chargerUtilisateurs]);

  const changerEtatCompte = async (utilisateur) => {
    if (!utilisateur?.id) {
      setErreur("Identifiant du compte introuvable.");
      return;
    }

    if (utilisateur.role === "COORDINATEUR") {
      setErreur("Un compte Coordinateur ne peut pas être bloqué depuis cette page.");
      return;
    }

    const bloquer = Boolean(utilisateur.actif);
    const action = bloquer ? "bloquer" : "debloquer";
    const verbe = bloquer ? "bloquer" : "débloquer";

    if (
      !window.confirm(
        `Confirmer : ${verbe} le compte de ${nomUtilisateur(utilisateur)} ?`
      )
    ) return;

    setErreur("");
    setMessage("");
    setActionEnCours(utilisateur.id);

    try {
      const resultat = await requeteAPI(
        `/utilisateurs/${utilisateur.id}/${action}/`,
        { method: "POST" }
      );

      setMessage(
        resultat?.detail ||
          `Le compte de ${nomUtilisateur(utilisateur)} a été ${bloquer ? "bloqué" : "débloqué"}.`
      );

      await chargerUtilisateurs();
    } catch (e) {
      setErreur(e.message || "Impossible de modifier l'état du compte.");
    } finally {
      setActionEnCours(null);
    }
  };

  const utilisateursFiltres = useMemo(() => {
    const terme = recherche.trim().toLocaleLowerCase();

    return utilisateurs.filter((u) => {
      const correspondRecherche =
        !terme ||
        [
          u?.nom,
          u?.prenom,
          u?.identifiant,
          u?.telephone,
          u?.email,
          u?.role,
          u?.role_libelle,
          u?.eglise_nom,
          u?.eglise?.nom,
        ]
          .filter(Boolean)
          .some((v) => String(v).toLocaleLowerCase().includes(terme));

      const correspondRole =
        filtreRole === "TOUS" || u.role === filtreRole;

      const correspondEtat =
        filtreEtat === "TOUS" ||
        (filtreEtat === "ACTIF" && Boolean(u.actif)) ||
        (filtreEtat === "BLOQUE" && !u.actif);

      return correspondRecherche && correspondRole && correspondEtat;
    });
  }, [utilisateurs, recherche, filtreRole, filtreEtat]);

  const comptesActifs = utilisateurs.filter((u) => u.actif).length;
  const comptesBloques = utilisateurs.length - comptesActifs;
  const administrateurs = utilisateurs.filter(
    (u) => ["ADMIN_LOCAL", "SUPERADMIN_INTL", "SUPERADMIN_NATIONAL", "COORDINATEUR"].includes(u.role)
  ).length;
  const pasteurs = utilisateurs.filter((u) => u.role === "PASTEUR").length;

  return (
    <main className="admin-global">
      <header className="ag-heading">
        <div>
          <div className="ag-eyebrow">EESAG · Administration centrale</div>
          <h2>Gestion des utilisateurs</h2>
          <p>Consulter les comptes et contrôler leur accès à la plateforme EESAG.</p>
        </div>

        <button
          type="button"
          className="btn btn-outline-secondary btn-sm"
          onClick={chargerUtilisateurs}
          disabled={chargement}
        >
          {chargement ? "Chargement..." : "↻ Actualiser"}
        </button>
      </header>

      {erreur && <div className="alert alert-danger ag-alert">{erreur}</div>}
      {message && <div className="alert alert-success ag-alert">{message}</div>}

      <section className="ag-stats">
        <div className="ag-stat ag-blue">
          <span className="ag-stat-label">Comptes enregistrés</span>
          <span className="ag-stat-value">{utilisateurs.length}</span>
        </div>
        <div className="ag-stat ag-green">
          <span className="ag-stat-label">Comptes actifs</span>
          <span className="ag-stat-value">{comptesActifs}</span>
        </div>
        <div className="ag-stat ag-red">
          <span className="ag-stat-label">Comptes bloqués</span>
          <span className="ag-stat-value">{comptesBloques}</span>
        </div>
        <div className="ag-stat ag-purple">
          <span className="ag-stat-label">Administrateurs et pasteurs</span>
          <span className="ag-stat-value">{administrateurs + pasteurs}</span>
        </div>
      </section>

      <section className="ag-panel">
        <div className="ag-toolbar">
          <h5>Liste de tous les utilisateurs</h5>

          <div className="ag-filters">
            <input
              type="search"
              className="ag-control ag-search"
              placeholder="Nom, identifiant, téléphone, église..."
              value={recherche}
              onChange={(e) => setRecherche(e.target.value)}
              aria-label="Rechercher un utilisateur"
            />

            <select
              className="ag-control"
              value={filtreRole}
              onChange={(e) => setFiltreRole(e.target.value)}
              aria-label="Filtrer par rôle"
            >
              <option value="TOUS">Tous les rôles</option>
              <option value="COORDINATEUR">Coordinateur</option>
              <option value="SUPERADMIN_INTL">Super administrateur international</option>
              <option value="SUPERADMIN_NATIONAL">Super administrateur national</option>
              <option value="ADMIN_LOCAL">Administrateur local</option>
              <option value="PASTEUR">Pasteur</option>
              <option value="MEMBRE">Membre</option>
            </select>

            <select
              className="ag-control"
              value={filtreEtat}
              onChange={(e) => setFiltreEtat(e.target.value)}
              aria-label="Filtrer par état du compte"
            >
              <option value="TOUS">Tous les états</option>
              <option value="ACTIF">Comptes actifs</option>
              <option value="BLOQUE">Comptes bloqués</option>
            </select>
          </div>
        </div>

        {chargement ? (
          <div className="ag-empty">Chargement des utilisateurs...</div>
        ) : utilisateursFiltres.length === 0 ? (
          <div className="ag-empty">Aucun compte ne correspond aux filtres.</div>
        ) : (
          <div className="ag-table-wrap">
            <table className="ag-table">
              <thead>
                <tr>
                  <th>Utilisateur</th>
                  <th>Identifiant</th>
                  <th>Rôle</th>
                  <th>Église de rattachement</th>
                  <th>Téléphone</th>
                  <th>État du compte</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {utilisateursFiltres.map((u) => (
                  <tr key={u.id ?? u.identifiant}>
                    <td>
                      <span className="ag-primary-text">{nomUtilisateur(u)}</span>
                      <span className="ag-secondary-text">{u.email || "E-mail non renseigné"}</span>
                    </td>
                    <td>{u.identifiant || "—"}</td>
                    <td>{badgeRole(u.role)}</td>
                    <td>{u.eglise_nom || u.eglise?.nom || "Administration nationale"}</td>
                    <td>{u.telephone || "—"}</td>
                    <td>
                      {u.actif ? (
                        <span className="ag-badge ag-badge-green">Actif</span>
                      ) : (
                        <span className="ag-badge ag-badge-red">Bloqué / inactif</span>
                      )}
                    </td>
                    <td>
                      {u.role === "COORDINATEUR" ? (
                        <span className="ag-badge ag-badge-gray">Compte protégé</span>
                      ) : (
                        <button
                          type="button"
                          className={`ag-action ${u.actif ? "ag-action-red" : "ag-action-green"}`}
                          disabled={actionEnCours === u.id}
                          onClick={() => changerEtatCompte(u)}
                        >
                          {actionEnCours === u.id
                            ? "Traitement..."
                            : u.actif
                              ? "Bloquer"
                              : "Débloquer"}
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <footer className="ag-footer">
          {utilisateursFiltres.length} résultat(s) affiché(s) sur {utilisateurs.length} compte(s).
          {" "}La création et la modification des comptes restent gérées dans Django Admin.
        </footer>
      </section>
    </main>
  );
}
