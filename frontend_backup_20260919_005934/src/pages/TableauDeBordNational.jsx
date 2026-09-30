import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ComposedChart,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import client from "../api/client";
import { useAuth } from "../context/AuthContext";

const arr = (value) => (Array.isArray(value) ? value : []);
const obj = (value) => (value && typeof value === "object" ? value : {});
const fmt = (value) => Number(value || 0).toLocaleString("fr-FR");
const COLORS = ["#18bfd1", "#5167f2", "#f7b64a", "#ef7185", "#34b27b"];

function StatCard({ icon, title, value, caption, accent }) {
  return (
    <article className={national-stat-card ${accent || ""}}>
      <div className="national-stat-icon">{icon}</div>
      <div className="national-stat-copy">
        <span>{title}</span>
        <strong>{value}</strong>
        <small>{caption}</small>
      </div>
    </article>
  );
}

function Empty({ children = "Aucune donnée disponible." }) {
  return <div className="national-empty">{children}</div>;
}

export default function TableauDeBordNational() {
  const { estCoordinateur, estBureauNationalGeneral, utilisateur } = useAuth();
  const [stats, setStats] = useState(null);
  const [erreur, setErreur] = useState("");

  useEffect(() => {
    if (!estCoordinateur && !estBureauNationalGeneral) return;
    let live = true;
    client
      .get("/stats/national/")
      .then((response) => {
        if (live) setStats(response.data || {});
      })
      .catch((error) => {
        if (live) {
          setErreur(
            error.response?.data?.detail ||
              "Impossible de charger le tableau de bord du Bureau national."
          );
        }
      });
    return () => {
      live = false;
    };
  }, [estCoordinateur, estBureauNationalGeneral]);

  if (!estCoordinateur && !estBureauNationalGeneral) {
    return <Navigate to="/bureaux" replace />;
  }

  if (erreur) {
    return (
      <div className="national-dashboard-shell">
        <div className="national-error">
          <strong>Tableau de bord indisponible</strong>
          <span>{erreur}</span>
        </div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="national-dashboard-shell">
        <div className="national-loading">
          <div className="loading-spinner" />
          <span>Chargement du tableau de bord…</span>
        </div>
      </div>
    );
  }

  const repartition = obj(stats?.repartition_membres);
  const finance = obj(stats?.finance);
  const activite = arr(stats?.evolution_eglises);
  const regions = arr(stats.eglises_par_region);
  const topEglises = arr(stats.membres_par_eglise_top20);
  const bureau = arr(stats.bureau_national);
  const age = [
    { name: "Enfants", value: Number(repartition.enfants || 0) },
    { name: "Jeunes", value: Number(repartition.jeunes || 0) },
    { name: "Adultes", value: Number(repartition.adultes || 0) },
  ];
  const sex = [
    { name: "Hommes", value: Number(repartition.hommes || 0) },
    { name: "Femmes", value: Number(repartition.femmes || 0) },
  ];
  const churches = Number(stats.nombre_eglises || 0);
  const activeChurches = Number(stats.nombre_eglises_actives || 0);
  const pendingChurches = Number(stats.eglises_a_activer || 0);
  const activationRate = churches ? Math.round((activeChurches / churches) * 100) : 0;
  const todayLabel = new Intl.DateTimeFormat("fr-FR", {
    weekday: "long",
    day: "2-digit",
    month: "long",
    year: "numeric",
  }).format(new Date());

  // Ne pas utiliser de hook ici : cette section est exécutée après les retours
  // conditionnels de chargement/erreur. Une ancienne version appelait useMemo
  // uniquement après le chargement des statistiques, ce qui changeait l'ordre
  // des hooks entre deux rendus et faisait planter toute la page.
  const activityData = activite.map((item) => ({
    mois: item.mois_label || item.mois,
    total: Number(item.total || 0),
    actives: Number(item.actives || 0),
  }));

  const radialData = [{ name: "Activation", value: activationRate, fill: "#19c1d2" }];

  return (
    <div className="national-dashboard-shell">
      <section className="national-hero">
        <div>
          <span className="national-kicker">
            {estCoordinateur ? "CENTRE DE CONTRÔLE EESAG" : "BUREAU NATIONAL"}
          </span>
          <h1>{estCoordinateur ? "Tableau de bord du réseau" : "Tableau de bord du Bureau national"}</h1>
          <p>
            {estCoordinateur
              ? "Vue consolidée du réseau EESAG, de l'activité nationale et des accès des structures."
              : "Vue consolidée des églises, des comptes de gestion et des activités relevant du Bureau national."}
          </p>
        </div>
        <div className="national-hero-meta">
          <span className="national-live"><i /> DONNÉES EN DIRECT</span>
          <strong>{todayLabel}</strong>
          <small>Connecté : {utilisateur?.prenom} {utilisateur?.nom}</small>
        </div>
      </section>

      <section className="national-stat-grid">
        <StatCard icon="◎" title="Églises actives" value={fmt(activeChurches)} caption={${fmt(churches)} églises recensées} accent="cyan" />
        <StatCard icon="!" title="À activer" value={fmt(pendingChurches)} caption="Activation depuis Django Admin" accent="orange" />
        <StatCard icon="♙" title="Membres actifs" value={fmt(repartition.total)} caption={${fmt(stats.comptes_admin_eglises)} administrateurs d'église} accent="purple" />
        <StatCard icon="◇" title="Comptes nationaux" value={fmt(stats.bureau_national_total)} caption="Bureau national" accent="green" />
      </section>

      <section className="national-reference-grid">
        <article className="national-card national-chart-card large">
          <div className="national-card-head">
            <div>
              <span className="national-card-kicker">ACTIVITÉ</span>
              <h2>Enregistrement des églises</h2>
              <p>Évolution des créations et des églises actives sur les derniers mois.</p>
            </div>
            <span className="national-chip">6 mois</span>
          </div>
          {activityData.length ? (
            <ResponsiveContainer width="100%" height={255}>
              <ComposedChart data={activityData} margin={{ top: 10, right: 10, left: -18, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#edf1f5" />
                <XAxis dataKey="mois" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: "#7c8b9a" }} />
                <YAxis allowDecimals={false} axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: "#7c8b9a" }} />
                <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e4e9ef" }} />
                <Legend iconType="circle" />
                <Bar dataKey="total" name="Créées" barSize={18} fill="#d9e0e8" radius={[6, 6, 0, 0]} />
                <Line type="monotone" dataKey="actives" name="Actives" stroke="#18bfd1" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} />
              </ComposedChart>
            </ResponsiveContainer>
          ) : <Empty />}
        </article>

        <article className="national-card national-progress-card">
          <div className="national-card-head">
            <div>
              <span className="national-card-kicker">RÉSEAU</span>
              <h2>Activation</h2>
              <p>Églises ouvertes à la plateforme.</p>
            </div>
            <span className="national-small-label">{fmt(activeChurches)} / {fmt(churches)}</span>
          </div>
          <div className="national-radial-wrap">
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={[{ value: 100 }]} dataKey="value" startAngle={90} endAngle={-270} innerRadius={75} outerRadius={92} stroke="none" fill="#eaf2f6" />
                <Pie data={radialData} dataKey="value" startAngle={90} endAngle={90 - activationRate * 3.6} innerRadius={75} outerRadius={92} stroke="none" cornerRadius={18}>
                  <Cell fill="#19bfd1" />
                </Pie>
              </PieChart>
            </ResponsiveContainer>
            <div className="national-radial-label"><strong>{activationRate}%</strong><span>activées</span></div>
          </div>
          <div className="national-progress-legend">
            <span><i className="dot-cyan" /> Actives <b>{fmt(activeChurches)}</b></span>
            <span><i className="dot-muted" /> À activer <b>{fmt(pendingChurches)}</b></span>
          </div>
          <div className="national-alert-box">
            <strong>Action Bureau national</strong>
            <span>L'activation et la désactivation des églises se font uniquement dans Django Admin.</span>
          </div>
        </article>

        <article className="national-card national-mini-chart">
          <div className="national-card-head">
            <div>
              <span className="national-card-kicker">MEMBRES</span>
              <h2>Répartition par sexe</h2>
            </div>
          </div>
          {sex.some((item) => item.value > 0) ? (
            <ResponsiveContainer width="100%" height={190}>
              <PieChart>
                <Pie data={sex} dataKey="value" nameKey="name" innerRadius={48} outerRadius={70} paddingAngle={4}>
                  {sex.map((_, index) => <Cell key={index} fill={COLORS[index]} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : <Empty />}
          <div className="national-legend-pills">
            {sex.map((item, index) => <span key={item.name}><i style={{ background: COLORS[index] }} /> {item.name} <b>{fmt(item.value)}</b></span>)}
          </div>
        </article>

        <article className="national-card national-chart-card">
          <div className="national-card-head">
            <div>
              <span className="national-card-kicker">GÉOGRAPHIE</span>
              <h2>Églises par région</h2>
            </div>
          </div>
          {regions.length ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={regions} margin={{ top: 10, right: 10, left: -18, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#edf1f5" />
                <XAxis dataKey="region__nom" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: "#7c8b9a" }} />
                <YAxis allowDecimals={false} axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: "#7c8b9a" }} />
                <Tooltip />
                <Bar dataKey="nb_eglises" name="Églises" fill="#5167f2" radius={[7, 7, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : <Empty />}
        </article>

        <article className="national-card national-mini-chart">
          <div className="national-card-head">
            <div>
              <span className="national-card-kicker">ÂGES</span>
              <h2>Répartition</h2>
            </div>
          </div>
          {age.some((item) => item.value > 0) ? (
            <ResponsiveContainer width="100%" height={190}>
              <BarChart data={age} margin={{ top: 10, right: 8, left: -24, bottom: 0 }}>
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: "#7c8b9a" }} />
                <YAxis allowDecimals={false} axisLine={false} tickLine={false} tick={{ fontSize: 9, fill: "#7c8b9a" }} />
                <Tooltip />
                <Bar dataKey="value" fill="#f7b64a" radius={[7, 7, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : <Empty />}
        </article>

        <article className="national-card national-top-card">
          <div className="national-card-head">
            <div>
              <span className="national-card-kicker">COMMUNAUTÉS</span>
              <h2>Églises les plus peuplées</h2>
            </div>
          </div>
          {topEglises.length ? (
            <div className="national-top-list">
              {topEglises.slice(0, 7).map((item, index) => (
                <div className="national-top-row" key={${item.eglise__nom}-${index}}>
                  <span className="rank">{index + 1}</span>
                  <div><b>{item.eglise__nom}</b><small>{fmt(item.nb)} membres actifs</small></div>
                  <strong>{fmt(item.nb)}</strong>
                </div>
              ))}
            </div>
          ) : <Empty />}
        </article>
      </section>

      <section className="national-bottom-grid">
        <article className="national-card national-finance-card">
          <div className="national-card-head">
            <div>
              <span className="national-card-kicker">FINANCES</span>
              <h2>Centre financier national</h2>
              <p>Montants relevant du périmètre national.</p>
            </div>
            <span className="national-finance-total"><small>Solde</small><strong>{fmt(finance.solde)} GNF</strong></span>
          </div>
          <div className="national-finance-grid">
            <div><span>Entrées</span><strong>{fmt(finance.entrees)} GNF</strong></div>
            <div><span>Sorties</span><strong>{fmt(finance.sorties)} GNF</strong></div>
            <div><span>Opérations</span><strong>{fmt(finance.transactions)}</strong></div>
          </div>
        </article>

        <article className="national-card national-governance-card">
          <div className="national-card-head">
            <div>
              <span className="national-card-kicker">GOUVERNANCE</span>
              <h2>Bureau national</h2>
            </div>
            <span className="national-small-label">{fmt(stats.bureau_national_total)} comptes</span>
          </div>
          {bureau.length ? (
            <div className="national-governance-list">
              {bureau.slice(0, 6).map((member) => (
                <div className="national-governance-row" key={member.id}>
                  <div className="national-avatar">{(member.prenom || "?").charAt(0)}{(member.nom || "?").charAt(0)}</div>
                  <div><b>{member.prenom} {member.nom}</b><small>{member.fonction_bureau_national || member.role_libelle || member.role}</small></div>
                  <span>{member.actif ? "Actif" : "En attente"}</span>
                </div>
              ))}
            </div>
          ) : <Empty>Aucun compte national à afficher.</Empty>}
        </article>
      </section>
    </div>
  );
}
