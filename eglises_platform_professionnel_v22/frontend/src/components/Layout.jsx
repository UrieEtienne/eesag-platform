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
    estAdminLocal,
    estPasteur,
    estGestionnaireEglise,
  } = useAuth();

  const location = useLocation();

  const [nonLues, setNonLues] = useState(0);
  const [annonces, setAnnonces] = useState([]);

  const [mobile, setMobile] = useState(() =>
    typeof window !== "undefined"
      ? window.matchMedia("(max-width: 767px)").matches
      : false
  );

  const [sidebarOuverte, setSidebarOuverte] = useState(() =>
    typeof window !== "undefined"
      ? !window.matchMedia("(max-width: 767px)").matches
      : true
  );

  // Responsive : fermeture par défaut sur mobile.
  useEffect(() => {
    const mediaQuery = window.matchMedia("(max-width: 767px)");

    const handleResize = (event) => {
      setMobile(event.matches);
      setSidebarOuverte(false);
    };

    mediaQuery.addEventListener("change", handleResize);

    return () => {
      mediaQuery.removeEventListener("change", handleResize);
    };
  }, []);

  // Empêcher le défilement de l'arrière-plan si le menu mobile est ouvert.
  useEffect(() => {
    document.body.classList.toggle(
      "menu-mobile-ouvert",
      mobile && sidebarOuverte
    );

    return () => {
      document.body.classList.remove("menu-mobile-ouvert");
    };
  }, [mobile, sidebarOuverte]);

  // Fermer le menu avec Échap.
  useEffect(() => {
    const handleEscape = (event) => {
      if (event.key === "Escape") {
        setSidebarOuverte(false);
      }
    };

    document.addEventListener("keydown", handleEscape);

    return () => {
      document.removeEventListener("keydown", handleEscape);
    };
  }, []);

  // Fermer le menu mobile après une navigation.
  const fermerSidebarSurMobile = () => {
    if (mobile) setSidebarOuverte(false);
  };

  // Charger les notifications et les annonces.
  useEffect(() => {
    if (!utilisateur) {
      setNonLues(0);
      setAnnonces([]);
      return;
    }

    client
      .get("/notifications/")
      .then((response) => {
        const data = response.data?.results || response.data || [];

        setNonLues(
          Array.isArray(data)
            ? data.filter((notification) => !notification.lu).length
            : 0
        );
      })
      .catch(() => setNonLues(0));

    client
      .get("/systeme/annonces/")
      .then((response) => {
        setAnnonces(
          Array.isArray(response.data) ? response.data : []
        );
      })
      .catch(() => setAnnonces([]));
  }, [utilisateur?.id, location.pathname]);

  // Liens de navigation.
  const link = (to, label, icon, badge = null) => (
    <NavLink
      key={`${to}-${label}`}
      to={to}
      end={to === "/"}
      onClick={fermerSidebarSurMobile}
      title={!sidebarOuverte ? label : undefined}
      aria-label={label}
      className={({ isActive }) =>
        `nav-link ${isActive ? "active" : ""}`
      }
    >
      <span className="nav-icon" aria-hidden="true">
        {icon}
      </span>

      {sidebarOuverte && (
        <>
          <span className="nav-label">{label}</span>
          {badge ? <b className="nav-badge">{badge}</b> : null}
        </>
      )}
    </NavLink>
  );

  // Accès à l'administration Django.
  const adminDjango = () => {
    const apiUrl = new URL(
      import.meta.env.VITE_API_URL || "/api/",
      window.location.origin
    );

    window.open(
      new URL("/admin/", apiUrl.origin).toString(),
      "_blank",
      "noopener,noreferrer"
    );
  };

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

  const basculerSidebar = () => {
    setSidebarOuverte((ouverte) => !ouverte);
  };

  const classesLayout = [
    "app-layout",
    sidebarOuverte ? "sidebar-open" : "sidebar-closed",
    mobile ? "layout-mobile" : "layout-desktop",
  ].join(" ");

  return (
    <div className={classesLayout}>
      {/* Overlay mobile : cliquer en dehors ferme le menu. */}
      {mobile && sidebarOuverte && (
        <button
          type="button"
          className="sidebar-overlay"
          aria-label="Fermer le menu"
          onClick={() => setSidebarOuverte(false)}
        />
      )}

      {/* Sidebar entièrement retirée de l'affichage lorsqu'elle est fermée. */}
      <aside
        className={`sidebar ${sidebarOuverte ? "sidebar-visible" : "sidebar-hidden"}`}
        aria-hidden={!sidebarOuverte}
        inert={!sidebarOuverte}
      >
        <div className="brand">
          <div className="brand-mark logo-brand">
            <img src="/assets/logo_eesag.jpg" alt="EESAG" />
          </div>

          {sidebarOuverte && (
            <div className="brand-text">
              <strong>EESAG</strong>
            </div>
          )}
        </div>

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

        
      <nav className="sidebar-nav" aria-label="Navigation principale">
        {/* Accueil toujours en premier */}
        {link("/", "Accueil", "⌂")}

        {sidebarOuverte && (
          <div className="nav-section-label">Navigation</div>
        )}

        {estCoordinateur &&
          link("/national", "Tableau national", "⌂")}

        {estBureauNationalGeneral &&
          link("/national", "Tableau de bord", "⌂")}

        {estBureauNational &&
          !estBureauNationalGeneral &&
          link("/bureaux", "Mon bureau", "◆")}

        {estGestionnaireEglise &&
          link("/eglise-dashboard", "Tableau de bord", "⌂")}

        {link("/notifications", "Notifications", "◌", nonLues || null)}
        {link("/profil", "Mon profil", "●")}
        {link("/reunions", "Réunions vidéo", "◉")}

        {/* Conserve ici tous les blocs d'administration et les autres liens existants. */}
      </nav>


        {sidebarOuverte && annonces.length > 0 && (
          <div className="sidebar-announcement">
            <span>NOUVEAUTÉ</span>
            <b>{annonces[0].titre}</b>
            <small>{annonces[0].message}</small>
          </div>
        )}

        <div className="sidebar-footer">
          {sidebarOuverte && (
            <NavLink
              className="team-link"
              to="/informations"
              onClick={fermerSidebarSurMobile}
            >
              <span>Équipe</span>
            </NavLink>
          )}

          <div className="user-mini">
            <div className="avatar avatar-photo">
              <img
                src={
                  utilisateur?.photo
                    ? mediaUrl(utilisateur.photo)
                    : "/assets/logo_eesag.jpg"
                }
                alt={utilisateur?.photo ? "Profil" : "EESAG"}
              />
            </div>

            {sidebarOuverte && (
              <div className="user-mini-info">
                <b>{utilisateur?.prenom} {utilisateur?.nom}</b>
                <small>
                  {utilisateur?.role_libelle || utilisateur?.role}
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

      {/* Contenu principal : prend toute la largeur lorsque le menu est fermé. */}
      <main className="contenu-principal">
        <header className="app-topbar">
          <div className="topbar-left">
            <button
              type="button"
              className="sidebar-toggle"
              onClick={basculerSidebar}
              aria-label={sidebarOuverte ? "Masquer le menu" : "Afficher le menu"}
              aria-expanded={sidebarOuverte}
              title={sidebarOuverte ? "Masquer le menu" : "Afficher le menu"}
            >
              <span aria-hidden="true">☰</span>
            </button>

            <div className="app-topbar-scope">
              <span className="topbar-overline">{scopeKind}</span>
              <strong className="topbar-scope-name">{scopeName}</strong>
            </div>
          </div>

          <div className="topbar-actions">
            <span className="topbar-user-name">
              {utilisateur?.prenom} {utilisateur?.nom}
            </span>

            <NavLink
              className="topbar-profile photo-profile"
              to="/profil"
              aria-label="Mon profil"
            >
              <img
                src={
                  utilisateur?.photo
                    ? mediaUrl(utilisateur.photo)
                    : "/assets/logo_eesag.jpg"
                }
                alt="Profil"
              />
            </NavLink>
          </div>
        </header>

        <div className="page-container">{children}</div>
      </main>
    </div>
  );
}