
import { useCallback, useEffect, useMemo, useState } from "react";
import client from "../api/client";
import { useAuth } from "../context/AuthContext";
import FormulaireMembre from "../components/FormulaireMembre";

function liste(data) {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.results)) return data.results;
  return [];
}

function ageMembre(dateNaissance) {
  if (!dateNaissance) return null;

  const naissance = new Date(dateNaissance);
  if (Number.isNaN(naissance.getTime())) return null;

  const aujourdHui = new Date();
  let age = aujourdHui.getFullYear() - naissance.getFullYear();

  const anniversairePasEncorePasse =
    aujourdHui.getMonth() < naissance.getMonth() ||
    (aujourdHui.getMonth() === naissance.getMonth() &&
      aujourdHui.getDate() < naissance.getDate());

  if (anniversairePasEncorePasse) age--;

  return age;
}

function initiales(membre) {
  return `${membre.prenom?.[0] || ""}${membre.nom?.[0] || ""}`.toUpperCase() || "M";
}

export default function Membres() {
  const {
    utilisateur,
    estNational,
    estGestionnaireEglise,
  } = useAuth();

  const [membres, setMembres] = useState([]);
  const [q, setQ] = useState("");
  const [sexeFiltre, setSexeFiltre] = useState("TOUS");
  const [departementFiltre, setDepartementFiltre] = useState("TOUS");
  const [show, setShow] = useState(false);
  const [chargement, setChargement] = useState(true);
  const [erreur, setErreur] = useState("");
  const [page, setPage] = useState(1);
  const elementsParPage = 10;

  const peutAjouter = Boolean(
    utilisateur?.eglise &&
    !estNational &&
    estGestionnaireEglise
  );

  const charger = useCallback(async () => {
    setChargement(true);
    setErreur("");

    try {
      const params = { role: "MEMBRE" };

      if (q.trim()) {
        params.search = q.trim();
      }

      const response = await client.get("/utilisateurs/", { params });
      setMembres(liste(response.data));
    } catch (error) {
      setMembres([]);
      setErreur(
        error.response?.data?.detail ||
          "Impossible de charger les membres de cette église."
      );
    } finally {
      setChargement(false);
    }
  }, [q]);

  useEffect(() => {
    const timer = setTimeout(charger, 250);
    return () => clearTimeout(timer);
  }, [charger]);

  useEffect(() => {
    setPage(1);
  }, [q, sexeFiltre, departementFiltre]);

  const departements = useMemo(() => {
    return [
      ...new Set(
        membres
          .map((m) => m.departement_nom)
          .filter(Boolean)
      ),
    ].sort((a, b) => a.localeCompare(b));
  }, [membres]);

  const membresFiltres = useMemo(() => {
    return membres.filter((membre) => {
      const sexe = String(membre.sexe || "").toUpperCase();

      const correspondSexe =
        sexeFiltre === "TOUS" ||
        sexe === sexeFiltre ||
        (sexeFiltre === "H" && sexe === "HOMME") ||
        (sexeFiltre === "F" && sexe === "FEMME");

      const correspondDepartement =
        departementFiltre === "TOUS" ||
        membre.departement_nom === departementFiltre;

      return correspondSexe && correspondDepartement;
    });
  }, [membres, sexeFiltre, departementFiltre]);

  const statistiques = useMemo(() => {
    const hommes = membres.filter((m) =>
      ["H", "HOMME"].includes(String(m.sexe || "").toUpperCase())
    ).length;

    const femmes = membres.filter((m) =>
      ["F", "FEMME"].includes(String(m.sexe || "").toUpperCase())
    ).length;

    const enfants = membres.filter((m) => {
      const age = ageMembre(m.date_naissance);
      return age !== null && age < 18;
    }).length;

    return {
      total: membres.length,
      hommes,
      femmes,
      enfants,
      departements: departements.length,
    };
  }, [membres, departements]);

  const totalPages = Math.max(
    1,
    Math.ceil(membresFiltres.length / elementsParPage)
  );

  const membresPage = membresFiltres.slice(
    (page - 1) * elementsParPage,
    page * elementsParPage
  );

  const reinitialiserFiltres = () => {
    setQ("");
    setSexeFiltre("TOUS");
    setDepartementFiltre("TOUS");
    setPage(1);
  };

  return (
    <div className="eesag-members-page">
      {/* EN-TÊTE */}
      <header className="members-heading">
        <div>
          <span className="members-eyebrow">
            ESPACE ÉGLISE LOCALE
          </span>

          <h1>Gestion des membres</h1>

          <p>
            Consultez et gérez le registre des membres de votre église.
          </p>
        </div>

        {peutAjouter && (
          <button
            type="button"
            className="members-add-button"
            onClick={() => setShow(true)}
          >
            <span>＋</span>
            Ajouter un membre
          </button>
        )}
      </header>

      {/* CARTES STATISTIQUES */}
      <section className="members-stats-grid">
        <article className="members-stat-card members-stat-orange">
          <div className="members-stat-icon">♙</div>
          <div>
            <span>Total des membres</span>
            <strong>{statistiques.total}</strong>
            <small>Comptes membres chargés</small>
          </div>
        </article>

        <article className="members-stat-card members-stat-blue">
          <div className="members-stat-icon">♂</div>
          <div>
            <span>Hommes</span>
            <strong>{statistiques.hommes}</strong>
            <small>Membres masculins</small>
          </div>
        </article>

        <article className="members-stat-card members-stat-pink">
          <div className="members-stat-icon">♀</div>
          <div>
            <span>Femmes</span>
            <strong>{statistiques.femmes}</strong>
            <small>Membres féminins</small>
          </div>
        </article>

        <article className="members-stat-card members-stat-green">
          <div className="members-stat-icon">♧</div>
          <div>
            <span>Enfants</span>
            <strong>{statistiques.enfants}</strong>
            <small>Moins de 18 ans, âge connu</small>
          </div>
        </article>

        <article className="members-stat-card members-stat-purple">
          <div className="members-stat-icon">▤</div>
          <div>
            <span>Départements</span>
            <strong>{statistiques.departements}</strong>
            <small>Départements représentés</small>
          </div>
        </article>
      </section>

      {/* ÉGLISE ET INFORMATION */}
      <div className="members-church-banner">
        <span className="members-banner-icon">♧</span>

        <div>
          <strong>
            {utilisateur?.eglise_nom || "Mon église"}
          </strong>

          <p>
            Registre des membres rattachés à cette église locale.
          </p>
        </div>
      </div>

      {/* ACCÈS ET PERMISSIONS */}
      <div className="members-access-banner">
        <span>🔒</span>

        <p>
          <strong>Accès sécurisé :</strong>{" "}
          les données affichées respectent les autorisations de votre compte.
          {peutAjouter
            ? " Vous pouvez ajouter un membre dans votre église."
            : " La consultation est disponible selon vos droits."}
        </p>
      </div>

      {erreur && (
        <div className="members-error" role="alert">
          <strong>Erreur :</strong> {erreur}
          <button type="button" onClick={charger}>
            Réessayer
          </button>
        </div>
      )}

      {/* TABLEAU */}
      <section className="members-table-card">
        <div className="members-table-heading">
          <div>
            <h2>♧ Liste des membres</h2>
            <p>
              {membresFiltres.length} résultat(s) correspondant aux filtres
            </p>
          </div>

          <span className="members-total-badge">
            {statistiques.total} membres
          </span>
        </div>

        {/* FILTRES */}
        <div className="members-filters">
          <div className="members-search">
            <span>⌕</span>
            <input
              type="search"
              placeholder="Rechercher nom, prénom ou matricule..."
              value={q}
              onChange={(e) => setQ(e.target.value)}
            />
          </div>

          <select
            aria-label="Filtrer par sexe"
            value={sexeFiltre}
            onChange={(e) => setSexeFiltre(e.target.value)}
          >
            <option value="TOUS">Tous les sexes</option>
            <option value="H">Hommes</option>
            <option value="F">Femmes</option>
          </select>

          <select
            aria-label="Filtrer par département"
            value={departementFiltre}
            onChange={(e) => setDepartementFiltre(e.target.value)}
          >
            <option value="TOUS">Tous les départements</option>
            {departements.map((nom) => (
              <option key={nom} value={nom}>
                {nom}
              </option>
            ))}
          </select>

          <button
            type="button"
            className="members-reset-button"
            onClick={reinitialiserFiltres}
          >
            Réinitialiser
          </button>
        </div>

        {/* TABLE */}
        <div className="members-table-scroll">
          <table className="members-table">
            <thead>
              <tr>
                <th>Actions</th>
                <th>Photo</th>
                <th>Matricule</th>
                <th>Nom complet</th>
                <th>Sexe</th>
                <th>Département</th>
                <th>Rôle dans l'église</th>
                <th>Fonction</th>
                <th>Téléphone</th>
              </tr>
            </thead>

            <tbody>
              {!chargement &&
                membresPage.map((membre) => (
                  <tr key={membre.id}>
                    <td>
                      <span className="members-view-action" title="Consultation">
                        ⌕
                      </span>
                    </td>

                    <td>
                      {membre.photo ? (
                        <img
                          className="members-avatar"
                          src={membre.photo}
                          alt={`${membre.prenom || ""} ${membre.nom || ""}`}
                        />
                      ) : (
                        <span className="members-avatar-placeholder">
                          {initiales(membre)}
                        </span>
                      )}
                    </td>

                    <td>
                      <span className="members-code">
                        {membre.identifiant || "—"}
                      </span>
                    </td>

                    <td>
                      <strong className="members-name">
                        {membre.prenom || ""} {membre.nom || ""}
                      </strong>
                    </td>

                    <td>{membre.sexe || "—"}</td>
                    <td>{membre.departement_nom || "—"}</td>
                    <td>{membre.role_eglise_nom || "—"}</td>
                    <td>{membre.fonction_eglise || "—"}</td>
                    <td>{membre.telephone || "—"}</td>
                  </tr>
                ))}
            </tbody>
          </table>

          {chargement && (
            <div className="members-empty-state">
              Chargement des membres...
            </div>
          )}

          {!chargement && !membresFiltres.length && !erreur && (
            <div className="members-empty-state">
              <span>♙</span>
              <strong>Aucun membre trouvé</strong>
              <p>Modifiez votre recherche ou vos filtres.</p>
            </div>
          )}
        </div>

        {/* PAGINATION LOCALE */}
        {!chargement && membresFiltres.length > 0 && (
          <div className="members-pagination">
            <span>
              Affichage de{" "}
              {(page - 1) * elementsParPage + 1}
              {" à "}
              {Math.min(page * elementsParPage, membresFiltres.length)}
              {" sur "}
              {membresFiltres.length} membres
            </span>

            <div>
              <button
                type="button"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                ← Précédent
              </button>

              <strong>
                {page} / {totalPages}
              </strong>

              <button
                type="button"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              >
                Suivant →
              </button>
            </div>
          </div>
        )}
      </section>

      {peutAjouter && (
        <p className="members-security-note">
          Les nouveaux comptes sont créés dans le périmètre de votre église.
          Le matricule est généré automatiquement par le système.
        </p>
      )}

      {/* FORMULAIRE EXISTANT CONSERVÉ */}
      {show && peutAjouter && (
        <FormulaireMembre
          egliseId={utilisateur?.eglise}
          onFerme={() => setShow(false)}
          onCree={() => {
            setShow(false);
            charger();
          }}
        />
      )}
    </div>
  );
}
