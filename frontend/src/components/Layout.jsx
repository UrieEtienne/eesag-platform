import { NavLink, useLocation } from "react-router-dom";
import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import client, { mediaUrl } from "../api/client";

export default function Layout({ children }) {
  const {
    utilisateur,
    deconnecter,

    estCoordinateur,
    estBureauNational,
    estGestionnaireEglise,
    estAdminLocal,
    estPasteur,

    peutGererEglises,
    peutAdministrerEglise,
    peutGererMembres,
    peutEnvoyerCourriers,
    peutRecevoirCourriers,
  } = useAuth();

  const [nonLues, setNonLues] = useState(0);
  const [annonces, setAnnonces] = useState([]);
  const [sidebarOuverte, setSidebarOuverte] = useState(true);

  const location = useLocation();

  /*
  |--------------------------------------------------------------------------
  | NOTIFICATIONS
  |--------------------------------------------------------------------------
  */

  useEffect(() => {
    if (!utilisateur) return;

    client
      .get("/notifications/")
      .then((r) => {
        const data = r.data?.results || r.data || [];

        setNonLues(
          Array.isArray(data)
            ? data.filter((n) => !n.lu).length
            : 0
        );
      })
      .catch(() => {});

    client
      .get("/systeme/annonces/")
      .then((r) => {
        setAnnonces(
          Array.isArray(r.data)
            ? r.data
            : r.data?.results || []
        );
      })
      .catch(() => {
        setAnnonces([]);
      });
  }, [utilisateur?.id, location.pathname]);

  /*
  |--------------------------------------------------------------------------
  | LIEN SIDEBAR
  |--------------------------------------------------------------------------
  */

  const link = (to, label, icon, badge = null) => (
    <NavLink
      key={`${to}-${label}`}
      to={to}
      end={to === "/"}
      className={({ isActive }) =>
          `nav-link ${isActive ? "active" : ""}`
      }
    >
      <span className="nav-icon">{icon}</span>

      {sidebarOuverte && (
        <span className="nav-label">{label}</span>
      )}

      {badge && sidebarOuverte ? (
        <b className="nav-badge">{badge}</b>
      ) : null}
    </NavLink>
  );

  /*
  |--------------------------------------------------------------------------
  | IDENTITE ESPACE
  |--------------------------------------------------------------------------
  */

  const scopeName = estCoordinateur
    ? "Coordinateur · Propriétaire du système"
    : estBureauNational
      ? "Bureau national"
      : utilisateur?.eglise_nom || "Église locale";

  const scopeKind = estCoordinateur
    ? "PROPRIÉTAIRE DU SYSTÈME"
    : estBureauNational
      ? "BUREAU NATIONAL"
      : "ÉGLISE LOCALE";

  return (
    <div
      className={`app-layout ${
        sidebarOuverte
          ? "sidebar-visible"
          : "sidebar-hidden"
      }`}
    >

      {/* ========================================================= */}
      {/* SIDEBAR                                                   */}
      {/* ========================================================= */}

      <aside className="sidebar">

        {/* LOGO */}

        <div className="brand">
          <div className="brand-mark logo-brand">
            <img
              src="/assets/logo_eesag.jpg"
              alt="EESAG"
            />
          </div>

          {sidebarOuverte && (
            <div>
              <strong>EESAG</strong>
              <small>Plateforme de gestion</small>
            </div>
          )}
        </div>

        {/* ESPACE */}

        {sidebarOuverte && (
          <div className="scope-card">
            <span>{scopeKind}</span>

            <b>{scopeName}</b>

            <small>
              {estCoordinateur
                ? "Contrôle global du système"
                : estBureauNational
                  ? "Administration nationale"
                  : "Données privées de votre église"}
            </small>
          </div>
        )}

        <nav className="sidebar-nav">

          {/* ===================================================== */}
          {/* ACCUEIL                                               */}
          {/* ===================================================== */}

          {sidebarOuverte && (
            <div className="nav-section-label">
              Navigation
            </div>
          )}

          {estCoordinateur &&
            link(
              "/national",
              "Tableau national",
              "⌂"
            )}

          {estBureauNational &&
            link(
              "/national",
              "Tableau de bord national",
              "⌂"
            )}

          {estGestionnaireEglise &&
            link(
              "/eglise-dashboard",
              "Tableau de bord",
              "⌂"
            )}

          {!estCoordinateur &&
            !estBureauNational &&
            !estGestionnaireEglise &&
            link(
              "/",
              "Accueil",
              "⌂"
            )}

          {/* ===================================================== */}
          {/* COORDINATEUR                                         */}
          {/* ===================================================== */}

          {estCoordinateur && (
            <>
              {sidebarOuverte && (
                <div className="nav-section-label">
                  ADMINISTRATION DU SYSTÈME
                </div>
              )}

              {link(
                "/admin-utilisateurs",
                "Admin · Utilisateurs",
                "♙"
              )}

              {link(
                "/admin-bureau-national",
                "Admin · Bureau national",
                "◆"
              )}

              {link(
                "/systeme",
                "Fonctionnalités système",
                "◈"
              )}

              {link(
                "/parametres",
                "Paramètres système",
                "⚙"
              )}

              {link(
                "/annonces-systeme",
                "Publications & mises à jour",
                "📢"
              )}
            </>
          )}

          {/* ===================================================== */}
          {/* BUREAU NATIONAL                                      */}
          {/* ===================================================== */}

          {estBureauNational && (
            <>
              {sidebarOuverte && (
                <div className="nav-section-label">
                  ADMINISTRATION NATIONALE
                </div>
              )}

              {link(
                "/admin-eglises",
                "Créer une église",
                "+"
              )}

              {link(
                "/eglises",
                "Liste des églises",
                "▤"
              )}

              {link(
                "/bureaux",
                "Bureau national",
                "◆"
              )}

              {link(
                "/documents",
                "Documents",
                "▣"
              )}

              {link(
                "/rapports",
                "Rapports",
                "▤"
              )}
            </>
          )}

          {/* ===================================================== */}
          {/* ADMINISTRATEUR LOCAL                                 */}
          {/* ===================================================== */}

          {estAdminLocal && (
            <>
              {sidebarOuverte && (
                <div className="nav-section-label">
                  ADMINISTRATION DE MON ÉGLISE
                </div>
              )}

              {link(
                "/eglise-administration",
                "Admin · Utilisateurs",
                "♙"
              )}

              {link(
                "/membres",
                "Membres",
                "♙"
              )}

              {link(
                "/departements",
                "Départements",
                "▤"
              )}

              {link(
                "/annexes",
                "Annexes",
                "⌘"
              )}

              {link(
                "/courriers",
                "Courriers",
                "✉"
              )}

              {link(
                "/documents",
                "Documents",
                "▣"
              )}

              {link(
                "/finances",
                "Comptabilité & projets",
                "₣"
              )}

              {link(
                "/rapports",
                "Rapports",
                "▤"
              )}
            </>
          )}

          {/* ===================================================== */}
          {/* PASTEUR                                              */}
          {/* ===================================================== */}

          {estPasteur && (
            <>
              {sidebarOuverte && (
                <div className="nav-section-label">
                  ESPACE PASTORAL
                </div>
              )}

              {link(
                "/membres",
                "Membres",
                "♙"
              )}

              {link(
                "/departements",
                "Départements",
                "▤"
              )}

              {link(
                "/courriers",
                "Courriers",
                "✉"
              )}

              {link(
                "/documents",
                "Documents",
                "▣"
              )}

              {link(
                "/rapports",
                "Rapports",
                "▤"
              )}
            </>
          )}

          {/* ===================================================== */}
          {/* SERVICES COMMUNS                                     */}
          {/* ===================================================== */}

          {sidebarOuverte && (
            <div className="nav-section-label">
              Services
            </div>
          )}

          {link(
            "/notifications",
            "Notifications",
            "◌",
            nonLues || null
          )}

          {link(
            "/reunions",
            "Réunions vidéo",
            "◉"
          )}

          {link(
            "/profil",
            "Mon profil",
            "●"
          )}

          {/* ===================================================== */}
          {/* AUTRES OUTILS COORDINATEUR                           */}
          {/* ===================================================== */}

          {estCoordinateur && (
            <>
              {sidebarOuverte && (
                <div className="nav-section-label">
                  Contrôle global
                </div>
              )}

              {link(
                "/eglises",
                "Toutes les églises",
                "◎"
              )}

              {link(
                "/documents",
                "Tous les documents",
                "▣"
              )}

              {link(
                "/finances",
                "Toutes les finances",
                "₣"
              )}

              {link(
                "/rapports",
                "Tous les rapports",
                "▤"
              )}
            </>
          )}

          {/* ===================================================== */}
          {/* MEMBRE                                               */}
          {/* ===================================================== */}

          {!estCoordinateur &&
            !estBureauNational &&
            !estAdminLocal &&
            !estPasteur && (
              <>
                {sidebarOuverte && (
                  <div className="nav-section-label">
                    Mon espace
                  </div>
                )}

                {link(
                  "/bureau-national",
                  "Bureau national",
                  "◆"
                )}

                {link(
                  "/notifications",
                  "Communications",
                  "◌"
                )}
              </>
            )}

        </nav>

        {/* ===================================================== */}
        {/* ANNONCE                                               */}
        {/* ===================================================== */}

        {sidebarOuverte && annonces.length > 0 && (
          <div className="sidebar-announcement">
            <span>NOUVEAUTÉ</span>

            <b>
              {annonces[0].titre}
            </b>

            <small>
              {annonces[0].message}
            </small>
          </div>
        )}

        {/* ===================================================== */}
        {/* FOOTER                                                */}
        {/* ===================================================== */}

        <div className="sidebar-footer">

          {sidebarOuverte && (
            <NavLink
              className="team-link"
              to="/informations"
            >
              <span>Équipe</span>
              <small>
                Équipe de développement
              </small>
            </NavLink>
          )}

          <div className="user-mini">

            <div className="avatar avatar-photo">
              {utilisateur?.photo ? (
                <img
                  src={mediaUrl(utilisateur.photo)}
                  alt="Profil"
                />
              ) : (
                <img
                  src="/assets/logo_eesag.jpg"
                  alt="EESAG"
                />
              )}
            </div>

            {sidebarOuverte && (
              <div>
                <b>
                  {utilisateur?.prenom}{" "}
                  {utilisateur?.nom}
                </b>

                <small>
                  {utilisateur?.role_libelle ||
                    utilisateur?.role}
                </small>
              </div>
            )}

          </div>

          {sidebarOuverte && (
            <button
              className="logout"
              onClick={deconnecter}
            >
              Déconnexion
            </button>
          )}

        </div>
      </aside>

      {/* ========================================================= */}
      {/* CONTENU                                                   */}
      {/* ========================================================= */}

      <main className="contenu-principal">

        <header className="app-topbar">

          <button
            type="button"
            className="sidebar-toggle"
            onClick={() =>
              setSidebarOuverte(
                (value) => !value
              )
            }
            title={
              sidebarOuverte
                ? "Masquer le menu"
                : "Afficher le menu"
            }
          >
            {sidebarOuverte ? "☰" : "☰"}
          </button>

          <div className="app-topbar-scope">
            <span className="topbar-overline">
              {scopeKind}
            </span>

            <strong className="topbar-scope-name">
              {scopeName}
            </strong>
          </div>

          <div className="topbar-actions">

            <span className="topbar-user-name">
              {utilisateur?.prenom}{" "}
              {utilisateur?.nom}
            </span>

            <NavLink
              className="topbar-profile photo-profile"
              to="/profil"
            >
              {utilisateur?.photo ? (
                <img
                  src={mediaUrl(
                    utilisateur.photo
                  )}
                  alt="Profil"
                />
              ) : (
                <img
                  src="/assets/logo_eesag.jpg"
                  alt="EESAG"
                />
              )}
            </NavLink>

          </div>

        </header>

        <div className="page-container">
          {children}
        </div>

      </main>

    </div>
  );
}
