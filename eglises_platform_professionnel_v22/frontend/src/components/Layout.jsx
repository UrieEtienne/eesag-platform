import { NavLink, useLocation } from "react-router-dom";
import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import client, { mediaUrl } from "../api/client";

export default function Layout({ children }) {
  const { utilisateur, deconnecter, estNational, estCoordinateur, estBureauNational, estGestionnaireEglise, peutGerer } = useAuth();
  const [nonLues, setNonLues] = useState(0);
  const location = useLocation();

  useEffect(() => {
    if (!utilisateur) return;
    client.get("/notifications/")
      .then((r) => setNonLues((r.data.results || r.data).filter((n) => !n.lu).length))
      .catch(() => {});
  }, [utilisateur, location.pathname]);

  const link = (to, label, icon, badge) => (
    <NavLink to={to} end={to === "/"} className="nav-link">
      <span className="nav-icon">{icon}</span>
      <span>{label}</span>
      {badge ? <b className="nav-badge">{badge}</b> : null}
    </NavLink>
  );

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark logo-brand"><img src="/assets/logo_eesag.jpg" alt="Assemblées de Dieu" /></div>
          <div><strong>EESAG</strong><small>Plateforme de gestion des églises</small></div>
        </div>
        <div className="scope-card">
          <span>{estNational ? "BUREAU NATIONAL" : "ESPACE ÉGLISE"}</span>
          <b>{estNational ? "Pilotage national" : utilisateur?.eglise_nom || "Mon église"}</b>
          <small>{estNational ? "Contrôle de l'ensemble du réseau" : "Données privées de votre église"}</small>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-section-label">Accueil</div>
          {link("/", estNational ? "Tableau national" : "Mon accueil", "⌂")}
          {link(estNational ? "/bureau-national" : "/bureaux", estNational ? "Bureau national" : "Mes bureaux", "◆")}
          {link("/notifications", "Notifications", "◌", nonLues || null)}
          {link("/profil", "Mon profil", "●")}
          {link("/reunions", "Réunions vidéo", "◉")}
          {estCoordinateur && link("/parametres", "Paramètres système", "⚙")}

          {estNational && <>
            <div className="nav-section-label">Pilotage national</div>
            {link("/eglises", "Églises & réseau", "◎")}
            {link("/recherche", "Recherche membre", "⌕")}
            {link("/geographie", "Géographie", "◇")}
            {link("/documents", "Documents nationaux", "▣")}
            {estCoordinateur && link("/courriers", "Affectations pastorales", "✉")}
            {link("/finances", "Comptabilité nationale", "₣")}
            {link("/rapports", "Rapports nationaux", "▤")}
            {link("/bureaux", "Bureaux nationaux", "◇")}
            {link("/ia", "Assistant IA", "✦")}
          </>}

          {!estNational && estGestionnaireEglise && <>
            <div className="nav-section-label">Gestion de l'église</div>
            {link("/membres", "Membres", "♙")}
            {link("/annexes", "Annexes", "⌘")}
            {link("/finances", "Comptabilité & projets", "₣")}
            {link("/documents", "Documents", "▣")}
            {utilisateur?.role === "PASTEUR" && link("/courriers", "Courriers & recommandations", "✉")}
            {link("/rapports", "Rapports", "▤")}
            {link("/administrateurs", "Administrateurs & droits", "⚙")}
            {link("/bureaux", "Bureaux internes", "◇")}
            {link("/ia", "Assistant IA", "✦")}
          </>}

          {!estNational && !peutGerer && <>
            <div className="nav-section-label">Services membre</div>
          </>}
        </nav>

        <div className="sidebar-footer">
          <div className="user-mini">
            <div className="avatar avatar-photo">{utilisateur?.photo ? <img src={mediaUrl(utilisateur.photo)} alt="Profil" /> : <img src="/assets/logo_eesag.jpg" alt="EESAG" />}</div>
            <div><b>{utilisateur?.prenom} {utilisateur?.nom}</b><small>{utilisateur?.role_libelle}</small></div>
          </div>
          <button className="logout" onClick={deconnecter}>Déconnexion</button>
        </div>
      </aside>

      <main className="contenu-principal">
        <header className="app-topbar">
          <div>
            <span className="topbar-title">EESAG</span>
            <span className="topbar-sep">/</span>
            <span>{estNational ? "Espace Bureau national" : utilisateur?.eglise_nom || "Espace Église"}</span>
          </div>
          <div className="topbar-actions">
            <span className="topbar-user-name">{utilisateur?.prenom} {utilisateur?.nom}</span>
            <NavLink className="topbar-profile photo-profile" to="/profil">{utilisateur?.photo ? <img src={mediaUrl(utilisateur.photo)} alt="Profil" /> : <img src="/assets/logo_eesag.jpg" alt="EESAG" />}</NavLink>
          </div>
        </header>
        <div className="page-container">{children}</div>
      </main>
    </div>
  );
}
