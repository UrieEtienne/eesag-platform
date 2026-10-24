import { NavLink, useLocation } from "react-router-dom";
import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import client, { mediaUrl } from "../api/client";

export default function Layout({ children }) {
  const {
    utilisateur,
    bureaux,
    deconnecter,

    estCoordinateur,
    estBureauNational,
    estBureauNationalGeneral,

    estAdminLocal,
    estPasteur,
    estGestionnaireEglise,

    peutAdministrerSysteme,
    peutGererEglises,
    peutAdministrerEglise,
    peutEnvoyerCourriers,
    peutRecevoirCourriers,
  } = useAuth();

  const [nonLues, setNonLues] = useState(0);
  const [annonces, setAnnonces] = useState([]);
  const [sidebarOuverte, setSidebarOuverte] = useState(true);

  const location = useLocation();

  /*
   * =========================
   * DONNEES
   * =========================
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
      .catch(() => {
        setNonLues(0);
      });

    client
      .get("/systeme/annonces/")
      .then((r) => {
        setAnnonces(
          Array.isArray(r.data)
            ? r.data
            : []
        );
      })
      .catch(() => {
        setAnnonces([]);
      });
  }, [utilisateur?.id, location.pathname]);

  /*
   * =========================
   * LIEN SIDEBAR
   * =========================
   */

    const link = (
        to,
        label,
        icon,
        badge = null
      ) => (
      <NavLink
        key={`${to}-${label}`}
        to={to}
        end={to === "/"}
        className={`nav-link ${isActive ? "active" : ""}`}
        title={!sidebarOuverte ? label : undefined}
      >
        <span className="nav-icon">
          {icon}
        </span>

        {sidebarOuverte && (
          <>
            <span>{label}</span>

            {badge ? (
              <b className="nav-badge">
                {badge}
              </b>
            ) : null}
          </>
        )}
      </NavLink>
    );

  /*
   * =========================
   * LIEN ADMIN DJANGO
   * =========================
   *
   * IMPORTANT :
   * La création/modification des comptes
   * reste côté Django Admin.
   */

  const adminDjango = () => {
    const apiUrl = new URL(
      import.meta.env.VITE_API_URL || "/api/",
      window.location.origin
    );

    const adminUrl = new URL(
      "/admin/",
      apiUrl.origin
    ).toString();

    window.open(
      adminUrl,
      "_blank",
      "noopener,noreferrer"
    );
  };

  /*
   * =========================
   * NOM DE L'ESPACE
   * =========================
   */

  const scopeName = estCoordinateur
    ? "Coordinateur · Propriétaire du système"
    : estBureauNational && !estBureauNationalGeneral
      ? (
          bureaux?.[0]?.nom ||
          "Mon bureau national"
        )
      : estBureauNationalGeneral
        ? "Bureau national"
        : utilisateur?.eglise_nom ||
          "Espace membre";

  const scopeKind = estCoordinateur
    ? "PROPRIÉTAIRE DU SYSTÈME"
    : estBureauNational
      ? "BUREAU NATIONAL"
      : "ÉGLISE LOCALE";

  /*
   * =========================
   * SIDEBAR
   * =========================
   */

  return ( <div className={`app-layout ${ sidebarOuverte ? "sidebar-open" : "sidebar-closed" }`} >
      <aside className="sidebar">

        {/* ================= BRAND ================= */}

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
              <small>
                Plateforme de gestion
              </small>
            </div>
          )}
        </div>

        {/* ================= ESPACE ================= */}

        {sidebarOuverte && (
          <div className="scope-card">
            <span>{scopeKind}</span>

            <b>{scopeName}</b>

            <small>
              {estCoordinateur
                ? "Contrôle global et paramètres système"
                : estBureauNational
                  ? "Gestion et supervision nationale"
                  : "Données privées de votre église"}
            </small>
          </div>
        )}

        {/* ================= NAVIGATION ================= */}

        <nav className="sidebar-nav">

          {sidebarOuverte && (
            <div className="nav-section-label">
              Navigation
            </div>
          )}

          {/* =========================================
              COORDINATEUR
             ========================================= */}

          {estCoordinateur &&
            link(
              "/national",
              "Tableau national",
              "⌂"
            )}

          {/* =========================================
              BUREAU NATIONAL GENERAL
             ========================================= */}

          {estBureauNationalGeneral &&
            link(
              "/national",
              "Tableau de bord",
              "⌂"
            )}

          {/* =========================================
              BUREAU NATIONAL SPECIFIQUE
             ========================================= */}

          {estBureauNational &&
            !estBureauNationalGeneral &&
            link(
              "/bureaux",
              "Mon bureau",
              "◆"
            )}

          {/* =========================================
              EGLISE LOCALE
             ========================================= */}

          {estGestionnaireEglise &&
            link(
              "/eglise-dashboard",
              "Tableau de bord",
              "⌂"
            )}

          {/* =========================================
              COMMUN
             ========================================= */}

          {link(
            "/notifications",
            "Notifications",
            "◌",
            nonLues || null
          )}

          {link(
            "/profil",
            "Mon profil",
            "●"
          )}

          {link(
            "/reunions",
            "Réunions vidéo",
            "◉"
          )}

          {/* =========================================
              COORDINATEUR
              CONTROLE GLOBAL
             ========================================= */}

          {estCoordinateur && (
  <>
              {sidebarOuverte && (
                <div className="nav-section-label">
                  ADMINISTRATION DU SYSTÈME
                </div>
              )}

              {link(
                "/admin",
                "Administration",
                "⚙"
              )}

              {link(
                "/admin-utilisateurs",
                "Admin · Utilisateurs",
                "♙"
              )}

              {link(
                "/admin-eglises",
                "Admin · Toutes les églises",
                "◎"
              )}
            </>
          )}

          {/* =========================================
              BUREAU NATIONAL
             ========================================= */}

          {estBureauNational && (
            <>
              {sidebarOuverte && (
                <div className="nav-section-label">
                  ADMINISTRATION NATIONALE
                </div>
              )}
              {link(
                "/admin-utilisateurs",
                "Admin · Utilisateurs",
                "♙"
              )}

              {estBureauNationalGeneral && (
                <>
                  {link(
                    "/eglises",
                    "Églises",
                    "◎"
                  )}

                  {link(
                    "/eglises",
                    "Créer une église",
                    "＋"
                  )}

                  {link(
                    "/eglises",
                    "Administrateurs des églises",
                    "♙"
                  )}
                </>
              )}

              {link(
                "/bureaux",
                "Mon bureau",
                "◇"
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

          {/* =========================================
              EGLISE LOCALE
             ========================================= */}

          {estGestionnaireEglise && (
            <>
              {sidebarOuverte && (
                <div className="nav-section-label">
                  GESTION DE L'ÉGLISE
                </div>
              )}

              {/* ADMIN LOCAL UNIQUEMENT */}

              {estAdminLocal && (
                <button
                  type="button"
                  className="nav-link nav-button-admin"
                  onClick={adminDjango}
                  title={
                    !sidebarOuverte
                      ? "Administration de l'église"
                      : undefined
                  }
                >
                  <span className="nav-icon">
                    ⚙
                  </span>

                  {sidebarOuverte && (
                    <span>
                      ADMIN ÉGLISE
                    </span>
                  )}
                </button>
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
                "/finances",
                "Comptabilité & projets",
                "₣"
              )}

              {link(
                "/documents",
                "Documents",
                "▣"
              )}

              {/* =====================================
                  COURRIERS
                 ===================================== */}

              {estAdminLocal &&
                link(
                  "/courriers/envoyer",
                  "Envoyer un courrier",
                  "✉"
                )}

              {(estAdminLocal ||
                estPasteur) &&
                link(
                  "/courriers/recus",
                  "Courriers reçus",
                  "📥"
                )}

              {link(
                "/rapports",
                "Rapports",
                "▤"
              )}
            </>
          )}

          {/* =========================================
              MEMBRE / AUTRES ROLES
             ========================================= */}

          {!estCoordinateur &&
            !estBureauNational &&
            !estGestionnaireEglise && (
              <>
                {link(
                  "/bureau-national",
                  "Bureau national",
                  "⌂"
                )}

                {link(
                  "/notifications",
                  "Communications",
                  "◌"
                )}
              </>
            )}
        </nav>

        {/* ================= ANNONCE ================= */}

        {sidebarOuverte &&
          annonces.length > 0 && (
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

        {/* ================= FOOTER ================= */}

        <div className="sidebar-footer">

          {sidebarOuverte && (
            <NavLink
              className="team-link"
              to="/informations"
            >
              <span>
                Équipe
              </span>

              <small>
                Équipe de développement
              </small>
            </NavLink>
          )}

          <div className="user-mini">

            <div className="avatar avatar-photo">
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

      {/* ================= CONTENU ================= */}

      <main className="contenu-principal">

        <header className="app-topbar">

          <div className="topbar-left">

            {/* BOUTON MASQUER / AFFICHER */}

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
              {sidebarOuverte
                ? "☰"
                : "☰"}
            </button>

            <div className="app-topbar-scope">
              <span className="topbar-overline">
                {scopeKind}
              </span>

              <strong className="topbar-scope-name">
                {scopeName}
              </strong>
            </div>
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