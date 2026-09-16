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
    estGestionnaireEglise,
  } = useAuth();

  const [nonLues, setNonLues] = useState(0);
  const [annonces, setAnnonces] = useState([]);
  const [features, setFeatures] = useState({});
  const location = useLocation();

  useEffect(() => {
    if (!utilisateur) return;

    client.get("/notifications/")
      .then((r) => {
        const data = r.data?.results || r.data || [];
        setNonLues(Array.isArray(data) ? data.filter((n) => !n.lu).length : 0);
      })
      .catch(() => {});

    client.get("/systeme/annonces/")
      .then((r) => setAnnonces(Array.isArray(r.data) ? r.data : []))
      .catch(() => setAnnonces([]));

    client.get("/systeme/fonctionnalites/")
      .then((r) => {
        const map = {};
        (Array.isArray(r.data) ? r.data : []).forEach((f) => {
          map[f.code] = f;
        });
        setFeatures(map);
      })
      .catch(() => setFeatures({}));
  }, [utilisateur?.id, location.pathname]);

  const featureActive = (feature) => {
    if (!feature) return true;
    if (!(feature in features)) return true;
    return features[feature]?.actif !== false;
  };

  const link = (to, label, icon, badge = null, feature = null) => {
    const disabled = !featureActive(feature);

    if (disabled) {
      return (
        <span
          key={to + label}
          className="nav-link nav-link-disabled"
          aria-disabled="true"
          title="Option désactivée par le propriétaire du système"
        >
          <span className="nav-icon">{icon}</span>
          <span>{label}</span>
          <span className="nav-lock">🔒</span>
          {badge ? <b className="nav-badge">{badge}</b> : null}
        </span>
      );
    }

    return (
      <NavLink
        key={to + label}
        to={to}
        end={to === "/"}
        className="nav-link"
      >
        <span className="nav-icon">{icon}</span>
        <span>{label}</span>
        {badge ? <b className="nav-badge">{badge}</b> : null}
      </NavLink>
    );
  };

  const scopeName = estCoordinateur
    ? "Coordinateur · Propriétaire du système"
    : estBureauNational && !estBureauNationalGeneral
      ? (bureaux[0]?.nom || "Mon bureau national")
      : estBureauNationalGeneral
        ? "Bureau national"
        : utilisateur?.eglise_nom || "Espace membre";

  const scopeKind = estCoordinateur
    ? "PROPRIÉTAIRE DU SYSTÈME"
    : estBureauNational
      ? "BUREAU NATIONAL"
      : "ÉGLISE LOCALE";

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark logo-brand">
            <img src="/assets/logo_eesag.jpg" alt="EESAG" />
          </div>
          <div>
            <strong>EESAG</strong>
            <small>Plateforme de gestion</small>
          </div>
        </div>

        <div className="scope-card">
          <span>{scopeKind}</span>
          <b>{scopeName}</b>
          <small>
            {estCoordinateur
              ? "Contrôle global et paramètres système"
              : estBureauNational
                ? "Espace national indépendant et privé"
                : "Données privées de votre église"}
          </small>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-section-label">Navigation</div>
          {estCoordinateur
            ? link("/national", "Tableau national", "⌂")
            : estBureauNationalGeneral
              ? link("/eglises", "Églises & activation", "◎", null, "eglises")
              : estBureauNational
                ? link("/bureaux", "Mon bureau", "◆", null, "bureaux")
                : estGestionnaireEglise
                  ? link("/eglise-dashboard", "Tableau de bord", "⌂")
                  : link("/bureau-national", "Accueil", "⌂")}

          {link("/notifications", "Notifications", "◌", nonLues || null, "notifications")}
          {link("/profil", "Mon profil", "●")}
          {link("/reunions", "Réunions vidéo", "◉", null, "reunions")}

          {(estCoordinateur || estBureauNationalGeneral) && (
            <>
              <div className="nav-section-label">Pilotage national</div>
              {link("/eglises", "Églises", "◎", null, "eglises")}
              {link("/administrateurs", "Administrateurs églises", "⚿", null, "administrateurs_eglises")}
              {link("/bureaux", "Bureaux nationaux", "◇", null, "bureaux")}
              {link("/documents", "Documents", "▣", null, "documents")}
              {link("/finances", "Comptabilité", "₣", null, "finances")}
              {link("/rapports", "Rapports", "▤", null, "rapports")}
            </>
          )}

          {estBureauNational && !estBureauNationalGeneral && (
            <>
              <div className="nav-section-label">Mon bureau</div>
              {link("/bureaux", "Composition annuelle", "◇", null, "bureaux")}
              {link("/documents", "Documents du bureau", "▣", null, "documents")}
              {link("/notifications", "Communications", "◌", null, "notifications")}
              {link("/rapports", "Rapports du bureau", "▤", null, "rapports")}
            </>
          )}

          {estGestionnaireEglise && (
            <>
              <div className="nav-section-label">Gestion de l'église</div>
              {link("/membres", "Membres", "♙", null, "membres")}
              {link("/departements", "Départements", "▤", null, "departements")}
              {link("/annexes", "Annexes", "⌘", null, "annexes")}
              {link("/finances", "Comptabilité & projets", "₣", null, "finances")}
              {link("/documents", "Documents", "▣", null, "documents")}
              {utilisateur?.role === "PASTEUR" && link("/courriers", "Courriers & recommandations", "✉", null, "courriers")}
              {link("/rapports", "Rapports", "▤", null, "rapports")}
              {link("/administrateurs", "Administrateurs & droits", "⚙", null, "administrateurs_eglises")}
              {link("/bureaux", "Bureaux internes", "◇", null, "bureaux")}
            </>
          )}

          {(estCoordinateur || estBureauNational || estGestionnaireEglise) && (
            <>
              <div className="nav-section-label">Configuration</div>
              {estCoordinateur && link("/parametres", "Paramètres système", "⚙")}
              {link("/systeme", "Mes fonctionnalités", "◈")}
            </>
          )}
        </nav>

        {annonces.length > 0 && (
          <div className="sidebar-announcement">
            <span>NOUVEAUTÉ</span>
            <b>{annonces[0].titre}</b>
            <small>{annonces[0].message}</small>
          </div>
        )}

        <div className="sidebar-footer">
          <NavLink className="team-link" to="/informations">
            <span>Équipe</span>
            <small>Équipe de développement</small>
          </NavLink>

          <div className="user-mini">
            <div className="avatar avatar-photo">
              {utilisateur?.photo ? (
                <img src={mediaUrl(utilisateur.photo)} alt="Profil" />
              ) : (
                <img src="/assets/logo_eesag.jpg" alt="EESAG" />
              )}
            </div>
            <div>
              <b>{utilisateur?.prenom} {utilisateur?.nom}</b>
              <small>{utilisateur?.role_libelle || utilisateur?.role}</small>
            </div>
          </div>
          <button className="logout" onClick={deconnecter}>Déconnexion</button>
        </div>
      </aside>

      <main className="contenu-principal">
        <header className="app-topbar">
          <div className="app-topbar-scope">
            <span className="topbar-overline">{scopeKind}</span>
            <strong className="topbar-scope-name">{scopeName}</strong>
          </div>
          <div className="topbar-actions">
            <span className="topbar-user-name">{utilisateur?.prenom} {utilisateur?.nom}</span>
            <NavLink className="topbar-profile photo-profile" to="/profil">
              {utilisateur?.photo ? (
                <img src={mediaUrl(utilisateur.photo)} alt="Profil" />
              ) : (
                <img src="/assets/logo_eesag.jpg" alt="EESAG" />
              )}
            </NavLink>
          </div>
        </header>
        <div className="page-container">{children}</div>
      </main>
    </div>
  );
}
