import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import client from "../api/client";

export default function TableauDeBordEglise() {
  const { utilisateur } = useAuth();
  const [stats, setStats] = useState(null);
  const [docs, setDocs] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [erreur, setErreur] = useState("");

  useEffect(() => {
    if (!utilisateur?.eglise) return;
    setErreur("");
    // Les statistiques constituent le socle de l'espace. Les documents et
    // notifications sont chargés indépendamment afin qu'une erreur sur un
    // module optionnel ne bloque pas toute l'église.
    client.get(`/stats/eglise/${utilisateur.eglise}/`)
      .then((r) => setStats(r.data))
      .catch((err) => setErreur(err.response?.data?.detail || "Impossible de charger les données de votre église."));

    client.get("/documents/")
      .then((r) => setDocs(r.data.results || r.data || []))
      .catch(() => setDocs([]));

    client.get("/notifications/")
      .then((r) => setNotifications(r.data.results || r.data || []))
      .catch(() => setNotifications([]));
  }, [utilisateur?.eglise]);

  if (erreur) return <p className="erreur">{erreur}</p>;
  if (!stats) return <div className="empty-state">Chargement de votre espace privé…</div>;

  const nonLues = notifications.filter((n) => !n.lu).length;
  const documentsRecus = docs.filter((d) => (d.destinataires_resume || []).some((x) => x.eglise === utilisateur.eglise)).length;

  return (
    <div>
      <div className="hero">
        <div>
          <span className="eyebrow">ESPACE PRIVÉ</span>
          <h2>{stats.eglise.nom}</h2>
          <p>Bienvenue dans le portail sécurisé de votre église. Votre équipe gère ici ses membres, départements, projets, annexes et échanges officiels.</p>
        </div>
        <div className="hero-code">{stats.eglise.code}</div>
      </div>

      <div className="grille-stats">
        <div className="stat-card"><span>👥</span><strong>{stats.repartition_membres.total}</strong><small>Membres actifs</small></div>
        <div className="stat-card"><span>🏛️</span><strong>{stats.nombre_departements}</strong><small>Départements</small></div>
        <div className="stat-card"><span>📄</span><strong>{documentsRecus}</strong><small>Documents accessibles</small></div>
        <div className="stat-card"><span>🔔</span><strong>{nonLues}</strong><small>Notifications non lues</small></div>
      </div>

      <div className="dashboard-grid">
        <section className="carte">
          <div className="section-header"><div><h3>Répartition de vos membres</h3><p>Vue synthétique de votre communauté.</p></div></div>
          <div className="mini-stats">
            <div><strong>{stats.repartition_membres.hommes}</strong><span>Hommes</span></div>
            <div><strong>{stats.repartition_membres.femmes}</strong><span>Femmes</span></div>
            <div><strong>{stats.repartition_membres.enfants}</strong><span>Enfants</span></div>
            <div><strong>{stats.repartition_membres.jeunes}</strong><span>Jeunes</span></div>
            <div><strong>{stats.repartition_membres.adultes}</strong><span>Adultes</span></div>
          </div>
        </section>

        <section className="carte">
          <div className="section-header"><div><h3>Dernières notifications</h3><p>Les informations qui concernent votre église.</p></div></div>
          {notifications.slice(0, 5).map((n) => <div className={`liste-item ${!n.lu ? "mise-en-avant" : ""}`} key={n.id}><div><b>{n.titre}</b><small>{n.message}</small></div><span>{new Date(n.date_creation).toLocaleDateString("fr-FR")}</span></div>)}
          {notifications.length === 0 && <div className="empty-state">Aucune notification.</div>}
        </section>
      </div>
    </div>
  );
}
