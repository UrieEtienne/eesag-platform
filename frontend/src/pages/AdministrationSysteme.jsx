import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./AdministrationSysteme.css";

const modules = [
  {
    titre: "Gestion des bureaux",
    description: "Administrer les bureaux nationaux, zonaux et locaux.",
    icone: "🏛️",
    lien: "/bureaux",
    action: "Ouvrir les bureaux",
    couleur: "primary",
  },
  {
    titre: "Administration des utilisateurs",
    description: "Créer et consulter les comptes utilisateurs autorisés.",
    icone: "👥",
    lien: "/admin-utilisateurs",
    action: "Gérer les utilisateurs",
    couleur: "success",
  },
  {
    titre: "Administration des églises",
    description: "Consulter les églises enregistrées et leur administration.",
    icone: "⛪",
    lien: "/eglises",
    action: "Gérer les églises",
    couleur: "warning",
  },
  {
    titre: "Paramètres du système",
    description: "Accéder aux outils de configuration du système.",
    icone: "⚙️",
    lien: "/parametres",
    action: "Ouvrir les paramètres",
    couleur: "secondary",
  },
];

export default function AdministrationSysteme() {
  const { utilisateur, estCoordinateur } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const niveauDemande = searchParams.get("niveau")?.toUpperCase();
  const niveauxAutorises = ["NATIONAL", "ZONAL", "LOCAL"];
  const niveauFiltre = niveauxAutorises.includes(niveauDemande)
    ? niveauDemande
    : null;

  const ouvrirBureaux = (niveau) => {
    navigate(niveau ? `/bureaux?niveau=${niveau}` : "/bureaux");
  };

  if (!estCoordinateur) {
    return (
      <main className="container-fluid py-4">
        <div className="alert alert-danger" role="alert">
          <h5 className="alert-heading">Accès refusé</h5>
          Cette page est réservée au Coordinateur du système EESAG.
        </div>
        <button
          type="button"
          className="btn btn-outline-secondary"
          onClick={() => navigate("/")}
        >
          Retour à l’accueil
        </button>
      </main>
    );
  }

  return (
    <main className="container-fluid px-3 px-lg-4 py-4 admin-systeme">
      <section
        className="card border-0 shadow-sm mb-4 overflow-hidden"
        style={{
          borderRadius: 18,
          background:
            "linear-gradient(120deg, #10233f 0%, #183d66 65%, #24547a 100%)",
          color: "#fff",
        }}
      >
        <div className="card-body p-4 p-lg-5">
          <div className="d-flex flex-column flex-lg-row justify-content-between align-items-lg-center gap-4">
            <div>
              <div
                className="small fw-bold text-uppercase mb-3"
                style={{ color: "#e5c878", letterSpacing: 2 }}
              >
              </div>

              <span className="badge rounded-pill text-bg-light px-3 py-2">
                Coordinateur du système
              </span>
            </div>

            <div
              className="text-center p-4"
              style={{
                minWidth: 175,
                borderRadius: 16,
                background: "rgba(255,255,255,0.09)",
                border: "1px solid rgba(255,255,255,0.15)",
              }}
            >
              <div style={{ fontSize: 42 }}>🛡️</div>
              <div className="fw-bold mt-2">Contrôle central</div>
              <small style={{ color: "#d9e4ef" }}>
                Accès système
              </small>
            </div>
          </div>
        </div>
      </section>

      <section className="mb-4">
        <div className="d-flex flex-column flex-md-row justify-content-between align-items-md-center gap-2 mb-3">
          <div>
            <h2 className="h4 fw-bold mb-1">
              Vos espaces d’administration
            </h2>
            <p className="text-muted mb-0">
              Utilisez les boutons pour ouvrir un module.
            </p>
          </div>

          <span className="badge rounded-pill text-bg-light border py-2 px-3">
            {modules.length} modules
          </span>
        </div>

        <div className="row g-3">
          {modules.map((module) => (
            <div className="col-12 col-md-6 col-xl-3" key={module.lien}>
              <article className="admin-module-card p-3">
                <div className="admin-module-icon" aria-hidden="true">
                  {module.icone}
                </div>
                <h3 className="admin-module-title">{module.titre}</h3>
                <p className="admin-module-description">{module.description}</p>
                {/* Conserve ici le bouton compact ci-dessus. */}
                <button
                  type="button"
                  className="btn admin-btn admin-btn-primary mt-2"
                  onClick={() => navigate(module.lien)}
                >
                  {module.action} →
                </button>
              </article>
            </div>
          ))}
        </div>
      </section>

      <section className="card border-0 shadow-sm mb-4">
        <div className="card-body p-4">
          <h2 className="h4 fw-bold mb-2">Gestion des bureaux</h2>
          <p className="text-muted mb-4">
            Choisissez le niveau de gouvernance à administrer.
          </p>

          <div className="row g-3">
            <div className="col-12 col-md-6 col-xl-3">
              <button
                type="button"
                className={`btn w-100 h-100 p-3 text-start ${
                  niveauFiltre === "NATIONAL"
                    ? "btn-primary"
                    : "btn-outline-primary"
                }`}
                onClick={() => ouvrirBureaux("NATIONAL")}
              >
                <span className="d-block fs-3 mb-2">🏛️</span>
                <strong className="d-block">Bureau national</strong>
                <small className="d-block mt-2">
                  Hommes, Femmes, Jeunesse et Enfants
                </small>
              </button>
            </div>

            <div className="col-12 col-md-6 col-xl-3">
              <button
                type="button"
                className={`btn w-100 h-100 p-3 text-start ${
                  niveauFiltre === "ZONAL"
                    ? "btn-success"
                    : "btn-outline-success"
                }`}
                onClick={() => ouvrirBureaux("ZONAL")}
              >
                <span className="d-block fs-3 mb-2">🗺️</span>
                <strong className="d-block">Bureaux zonaux</strong>
                <small className="d-block mt-2">
                  Structures territoriales et zones
                </small>
              </button>
            </div>

            <div className="col-12 col-md-6 col-xl-3">
              <button
                type="button"
                className={`btn w-100 h-100 p-3 text-start ${
                  niveauFiltre === "LOCAL"
                    ? "btn-warning"
                    : "btn-outline-warning"
                }`}
                onClick={() => ouvrirBureaux("LOCAL")}
              >
                <span className="d-block fs-3 mb-2">⛪</span>
                <strong className="d-block">Bureaux locaux</strong>
                <small className="d-block mt-2">
                  Bureaux rattachés aux églises
                </small>
              </button>
            </div>

            <div className="col-12 col-md-6 col-xl-3">
              <button
                type="button"
                className="btn btn-outline-secondary w-100 h-100 p-3 text-start"
                onClick={() => navigate("/bureaux?vue=composition")}
              >
                <span className="d-block fs-3 mb-2">👥</span>
                <strong className="d-block">Composition des bureaux</strong>
                <small className="d-block mt-2">
                  Membres, postes, photos et mandats
                </small>
              </button>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
