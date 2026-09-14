import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import client from "../api/client";

function formatTime(date) {
  return new Intl.DateTimeFormat("fr-FR", { hour: "2-digit", minute: "2-digit" }).format(date);
}

function formatDate(date) {
  return new Intl.DateTimeFormat("fr-FR", { weekday: "short", day: "2-digit", month: "short", year: "numeric" }).format(date);
}

function initials(user) {
  return `${user?.prenom?.[0] || ""}${user?.nom?.[0] || ""}`.toUpperCase();
}

export default function Accueil() {
  const { utilisateur, estNational, peutGerer } = useAuth();
  const [now, setNow] = useState(new Date());
  const [stats, setStats] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [erreur, setErreur] = useState("");

  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    if (!utilisateur) return;
    setErreur("");
    const requests = [client.get("/notifications/")];
    if (estNational) requests.push(client.get("/stats/national/"));
    else if (utilisateur.eglise) requests.push(client.get(`/stats/eglise/${utilisateur.eglise}/`));

    Promise.all(requests)
      .then((responses) => {
        const notificationData = responses[0].data;
        setNotifications(notificationData.results || notificationData || []);
        setStats(responses[1]?.data || null);
      })
      .catch(() => setErreur("Impossible de charger le centre de contrôle."));
  }, [utilisateur?.id, utilisateur?.eglise, estNational]);

  const unread = notifications.filter((n) => !n.lu).length;
  const recent = notifications.slice(0, 4);
  const displayName = `${utilisateur?.prenom || ""} ${utilisateur?.nom || ""}`.trim();
  const perimeter = estNational ? "Bureau national" : utilisateur?.eglise_nom || "Mon église";

  const kpis = useMemo(() => {
    if (estNational && stats) {
      return [
        { label: "Églises actives", value: stats.nombre_eglises_actives ?? 0, meta: `${stats.nombre_eglises ?? 0} recensées`, tone: "cyan" },
        { label: "Membres actifs", value: stats.repartition_membres?.total ?? 0, meta: "Réseau national", tone: "blue" },
        { label: "Bureau national", value: stats.bureau_national?.length ?? 0, meta: "Membres en fonction", tone: "green" },
        { label: "Notifications", value: unread, meta: "À traiter", tone: "pink" },
      ];
    }
    return [
      { label: "Membres actifs", value: stats?.repartition_membres?.total ?? 0, meta: utilisateur?.eglise_nom || "Votre église", tone: "cyan" },
      { label: "Départements", value: stats?.nombre_departements ?? 0, meta: "Structure interne", tone: "blue" },
      { label: "Notifications", value: unread, meta: "Nouvelles informations", tone: "green" },
      { label: "Accès", value: peutGerer ? "GESTION" : "MEMBRE", meta: "Périmètre sécurisé", tone: "pink" },
    ];
  }, [estNational, stats, unread, utilisateur?.eglise_nom, peutGerer]);

  return (
    <div className="console-page">
      <div className="console-headline">
        <div>
          <span className="console-kicker">EESAG · CENTRE DE CONTRÔLE</span>
          <h1>{estNational ? "Pilotage national" : "Espace de contrôle de votre église"}</h1>
          <p>{displayName} · {perimeter}</p>
        </div>
        <div className="console-head-actions">
          <span className="console-status"><i /> En ligne</span>
          <div className="console-user"><span>{initials(utilisateur)}</span><div><b>{displayName}</b><small>{utilisateur?.role_libelle}</small></div></div>
        </div>
      </div>

      <section className="control-surface">
        <aside className="control-rail">
          <div className="control-rail-brand logo-rail"><img src="/assets/logo_eesag.jpg" alt="EESAG" /></div>
          <Link to="/" className="control-rail-item active" title="Accueil">⌂</Link>
          <Link to="/notifications" className="control-rail-item" title="Notifications">◌</Link>
          <Link to="/bureau-national" className="control-rail-item" title="Bureau national">★</Link>
          {estNational && <Link to="/eglises" className="control-rail-item" title="Églises">◎</Link>}
          {!estNational && peutGerer && <Link to="/membres" className="control-rail-item" title="Membres">♙</Link>}
          <Link to="/profil" className="control-rail-item" title="Profil">●</Link>
          <div className="control-rail-bottom"><span>●</span></div>
        </aside>

        <div className="control-main">
          <div className="control-topline">
            <div className="control-location"><span>SECURE /</span> {estNational ? "NATIONAL OPERATIONS" : "CHURCH OPERATIONS"}</div>
            <div className="control-date">{formatDate(now)}</div>
          </div>

          <div className="control-grid">
            <section className="control-card security-card">
              <div className="control-card-head"><span>SÉCURITÉ</span><i>•••</i></div>
              <div className="security-center"><div className="security-shield">◈</div><strong>{estNational ? "RÉSEAU" : "ÉGLISE"}</strong><small>Accès autorisé</small></div>
              <div className="security-points"><span><i className="ok" /> Session active</span><span><i className="ok" /> Périmètre vérifié</span></div>
            </section>

            <section className="control-card time-card">
              <div className="time-label">CENTRE DE CONTRÔLE</div>
              <div className="time-value">{formatTime(now)}</div>
              <div className="time-date">{formatDate(now)}</div>
              <div className="time-foot"><span>UTC+0</span><span>{perimeter}</span></div>
            </section>

            <section className="control-card notifications-card">
              <div className="control-card-head"><span>NOTIFICATIONS</span><Link to="/notifications">Voir tout →</Link></div>
              <div className="notification-count"><strong>{unread}</strong><small>non lue(s)</small></div>
              <div className="notification-list-mini">
                {recent.map((n) => <Link to="/notifications" key={n.id} className="mini-notif"><span className={`mini-dot ${n.lu ? "read" : ""}`} /><div><b>{n.titre}</b><small>{n.message}</small></div></Link>)}
                {!recent.length && <div className="console-empty">Aucune nouvelle notification.</div>}
              </div>
            </section>

            <section className="control-card weather-like-card">
              <div className="control-card-head"><span>ÉTAT DU RÉSEAU</span><i>Live</i></div>
              <div className="network-gauge"><div className="gauge-ring"><b>{estNational ? stats?.nombre_eglises_actives ?? 0 : stats?.repartition_membres?.total ?? 0}</b><small>{estNational ? "églises actives" : "membres"}</small></div></div>
              <div className="network-stats"><span><b>{kpis[0].value}</b>{kpis[0].label}</span><span><b>{kpis[1].value}</b>{kpis[1].label}</span></div>
            </section>

            <section className="control-card metrics-card">
              <div className="control-card-head"><span>INDICATEURS</span><span className="tiny-live">● TEMPS RÉEL</span></div>
              <div className="metric-dial-grid">
                {kpis.map((kpi, index) => (
                  <div className={`metric-dial tone-${kpi.tone}`} key={kpi.label}>
                    <div className="dial-circle"><b>{kpi.value}</b></div>
                    <strong>{kpi.label}</strong>
                    <small>{kpi.meta}</small>
                  </div>
                ))}
              </div>
            </section>

            <section className="control-card quick-card">
              <div className="control-card-head"><span>ACCÈS RAPIDE</span></div>
              <div className="quick-console-links">
                <Link to="/profil"><b>01</b><span>Mon profil</span><i>↗</i></Link>
                <Link to="/bureau-national"><b>02</b><span>Bureau national</span><i>↗</i></Link>
                <Link to="/notifications"><b>03</b><span>Notifications</span><i>↗</i></Link>
                {peutGerer && <Link to={estNational ? "/eglises" : "/membres"}><b>04</b><span>{estNational ? "Réseau des églises" : "Membres"}</span><i>↗</i></Link>}
              </div>
            </section>
          </div>
        </div>
      </section>

      {erreur && <div className="console-error">{erreur}</div>}
    </div>
  );
}
