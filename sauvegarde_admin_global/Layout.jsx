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
    estBureauNationalGeneral,
    estGestionnaireEglise,
    estAdminLocal,
    estPasteur,
  } = useAuth();

  const [nonLues, setNonLues] = useState(0);
  const [annonces, setAnnonces] = useState([]);
  const [sidebarOuverte, setSidebarOuverte] = useState(true);

  const [mobile, setMobile] = useState(
    () => window.matchMedia("(max-width: 767px)").matches
  );

  useEffect(() => {
    const mediaQuery = window.matchMedia("(max-width: 767px)");

    const handleResize = (event) => {
      setMobile(event.matches);

      if (event.matches) {
        setSidebarOuverte(false);
      }
    };

    handleResize(mediaQuery);

    mediaQuery.addEventListener("change", handleResize);

    return () => {
      mediaQuery.removeEventListener("change", handleResize);
    };
  }, []);

  useEffect(() => {
    document.body.classList.toggle(
      "menu-mobile-ouvert",
      mobile && sidebarOuverte
    );

    return () => {
      document.body.classList.remove("menu-mobile-ouvert");
    };
  }, [mobile, sidebarOuverte]);

  const fermerSidebarSurMobile = () => {
    if (mobile) {
      setSidebarOuverte(false);
    }
  };

  const location = useLocation();

  /*
  |--------------------------------------------------------------------------
  | URL DES ADMINISTRATIONS DJANGO
  |--------------------------------------------------------------------------
  */

  // Administration Django principale : Coordinateur du système.
  const djangoAdminUrl =
    import.meta.env.VITE_DJANGO_ADMIN_URL ||
    (import.meta.env.DEV
      ? "http://127.0.0.1:8000/admin/"
      : "/admin/");

  // Administration Django séparée : Bureau national général.
  const djangoAdminNationalUrl =
    import.meta.env.VITE_DJANGO_ADMIN_NATIONAL_URL ||
    (import.meta.env.DEV
      ? "http://127.0.0.1:8000/admin-national/"
      : "/admin-national/");

  /*
  |--------------------------------------------------------------------------
  | NOTIFICATIONS ET ANNONCES
  |--------------------------------------------------------------------------
  */

  useEffect(() => {
    if (!utilisateur) {
      setNonLues(0);
      setAnnonces([]);
      return;
    }

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
            : r.data?.results || []
        );
      })
      .catch(() => {
        setAnnonces([]);
      });
  }, [utilisateur?.id, location.pathname]);

  /*
  |--------------------------------------------------------------------------
  | LIEN DE NAVIGATION
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
  | IDENTITÉ DE L'ESPACE
  |--------------------------------------------------------------------------
  */

  const nomEglise =
    utilisateur?.eglise_nom ||
    utilisateur?.eglise?.nom ||
    "Mon église";

  const scopeName = estCoordinateur
    ? "Coordinateur · Propriétaire du système"
    : estBureauNational
      ? "Bureau national"
      : nomEglise;

  const scopeKind = estCoordinateur
    ? "PROPRIÉTAIRE DU SYSTÈME"
    : estBureauNational
      ? "BUREAU NATIONAL"
      : "MON ÉGLISE";

  return (
    <div
      className={`app-layout ${
        sidebarOuverte
          ? "sidebar-visible"
          : "sidebar-hidden"
      }`}
    >
      {/* SIDEBAR */}

      <aside className="sidebar">
        {/* LOGO */}

        <div className="brand">
          <div className="brand-mark logo-brand">
            <img src="/assets/logo_eesag.jpg" alt="EESAG" />
          </div>

          {sidebarOuverte && (
            <div>
              <strong>EESAG</strong>
            </div>
          )}
        </div>

        {/* IDENTITÉ DE L'ESPACE */}

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
        {/* ACCUEIL — TOUJOURS EN PREMIÈRE POSITION */}
        {link("/", "Accueil", "⌂")}

        {/* TABLEAUX DE BORD SELON LE PROFIL */}
        {estCoordinateur &&
          link("/national", "Tableau national", "⌂")}

        {estBureauNational &&
          link("/national", "Tableau de bord national", "⌂")}

        {estGestionnaireEglise &&
          link("/eglise-dashboard", "Tableau de bord", "⌂")}

        {/* COORDINATEUR : ADMINISTRATION DJANGO */}
        {estCoordinateur && (
          <a
            href={djangoAdminUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="nav-link django-admin-link"
            title="Ouvrir l'administration Django du Coordinateur"
          >
            <span className="nav-icon">⚙</span>
            {sidebarOuverte && (
              <span className="nav-label">
                Administration Django
              </span>
            )}
          </a>
        )}

        {/* BUREAU NATIONAL */}
        {estBureauNational && (
          <>
            {sidebarOuverte && (
              <div className="nav-section-label">
                ADMINISTRATION NATIONALE
              </div>
            )}

            {link("/eglises", "Liste des églises", "▤")}

            {/* ADMIN DJANGO : BUREAU NATIONAL GÉNÉRAL */}
            {estBureauNationalGeneral && (
              <a
                href={djangoAdminNationalUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="nav-link django-admin-link"
                title="Créer et gérer les églises dans Django Admin"
              >
                <span className="nav-icon">⚙</span>
                {sidebarOuverte && (
                  <span className="nav-label">
                    Admin Django · Créer des églises
                  </span>
                )}
              </a>
            )}

            {link("/bureaux", "Bureau national", "◆")}
            {link("/documents", "Documents", "▣")}
            {link("/rapports", "Rapports", "▤")}
          </>
        )}

        {/* ADMINISTRATEUR LOCAL */}
        {estAdminLocal && (
          <>
            {sidebarOuverte && (
              <div className="nav-section-label">
                ADMINISTRATION DE MON ÉGLISE
              </div>
            )}

            {link("/eglise-administration", "Admin · Utilisateurs", "♙")}
            {link("/membres", "Membres", "♙")}
            {link("/departements", "Départements", "▤")}
            {link("/annexes", "Annexes", "⌘")}
            {link("/courriers", "Courriers", "✉")}
            {link("/documents", "Documents", "▣")}
            {link("/finances", "Comptabilité & projets", "₣")}
            {link("/rapports", "Rapports", "▤")}
          </>
        )}

        {/* PASTEUR */}
        {estPasteur && (
          <>
            {sidebarOuverte && (
              <div className="nav-section-label">
                ESPACE PASTORAL
              </div>
            )}

            {link("/membres", "Membres", "♙")}
            {link("/departements", "Départements", "▤")}
            {link("/courriers", "Courriers", "✉")}
            {link("/documents", "Documents", "▣")}
            {link("/rapports", "Rapports", "▤")}
          </>
        )}

        {/* SERVICES COMMUNS */}
        {link("/notifications", "Notifications", "◌", nonLues || null)}
        {link("/reunions", "Réunions vidéo", "◉")}
        {link("/profil", "Mon profil", "●")}
        {link("/a-propos", "À propos", "ⓘ")}
        {link("/parametres-interface", "Paramètres", "⚙")}
        {link("/dons", "Faire un don", "❤")}
        {link("/partager", "Partager l'application", "↗")}

        {/* CONTRÔLE GLOBAL DU COORDINATEUR */}
        {estCoordinateur && (
          <>
            {sidebarOuverte && (
              <div className="nav-section-label">
                Contrôle global
              </div>
            )}

            {link("/eglises", "Toutes les églises", "◎")}
            {link("/documents", "Tous les documents", "▣")}
            {link("/finances", "Toutes les finances", "₣")}
            {link("/rapports", "Tous les rapports", "▤")}
          </>
        )}

        {/* ESPACE MEMBRE */}
        {!estCoordinateur &&
          !estBureauNational &&
          !estAdminLocal &&
          !estPasteur && (
            <>
              {link("/bureau-national", "Bureau national", "◆")}
              {link("/bible", "Bible", "📖")}
              {link("/dictionnaire-biblique", "Dictionnaire biblique", "📚")}
              {link("/localisation", "Localisation", "📍")}
              {link("/notifications", "Communications", "◌")}
            </>
          )}
      </nav>

        {/* ANNONCES */}

        {sidebarOuverte && annonces.length > 0 && (
          <div className="sidebar-announcement">
            <span>NOUVEAUTÉ</span>
            <b>{annonces[0].titre}</b>
            <small>{annonces[0].message}</small>
          </div>
        )}

        {/* PIED DE LA SIDEBAR */}

        <div className="sidebar-footer">
          {sidebarOuverte && (
            <NavLink
              className="team-link"
              to="/informations"
            >
              <span>Équipe</span>
              <small>Équipe de développement</small>
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
                  {utilisateur?.prenom} {utilisateur?.nom}
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
              type="button"
              className="logout"
              onClick={deconnecter}
            >
              Déconnexion
            </button>
          )}
        </div>
      </aside>

      {/* CONTENU PRINCIPAL */}

      <main className="contenu-principal">
        <header className="app-topbar">
          <button
            type="button"
            className="sidebar-toggle"
            onClick={() =>
              setSidebarOuverte((value) => !value)
            }
            title={
              sidebarOuverte
                ? "Masquer le menu"
                : "Afficher le menu"
            }
          >
            ☰
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
              {utilisateur?.prenom} {utilisateur?.nom}
            </span>

            <NavLink
              className="topbar-profile photo-profile"
              to="/profil"
            >
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