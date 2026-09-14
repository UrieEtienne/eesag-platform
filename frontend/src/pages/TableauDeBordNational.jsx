import { useEffect, useState } from "react";
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from "recharts";
import client from "../api/client";

const COULEURS = ["#1a3c5e", "#c9a227", "#2e7d32", "#c0392b", "#2c5a86", "#7c3aed"];

export default function TableauDeBordNational() {
  const [stats, setStats] = useState(null);
  const [erreur, setErreur] = useState("");

  useEffect(() => {
    client.get("/stats/national/").then((res) => setStats(res.data)).catch(() => setErreur("Impossible de charger les statistiques."));
  }, []);

  if (erreur) return <p className="erreur">{erreur}</p>;
  if (!stats) return <p>Chargement des statistiques...</p>;

  const donneesRepartition = [
    { nom: "Hommes", valeur: stats.repartition_membres.hommes },
    { nom: "Femmes", valeur: stats.repartition_membres.femmes },
  ];
  const donneesAge = [
    { nom: "Enfants", valeur: stats.repartition_membres.enfants },
    { nom: "Jeunes", valeur: stats.repartition_membres.jeunes },
    { nom: "Adultes", valeur: stats.repartition_membres.adultes },
  ];

  return (
    <div>
      <div className="barre-superieure"><h2>Tableau de bord national</h2></div>

      <div className="grille-stats">
        <div className="carte">
          <div className="stat-chiffre">{stats.nombre_eglises}</div>
          <div className="stat-libelle">Églises recensées</div>
        </div>
        <div className="carte">
          <div className="stat-chiffre">{stats.nombre_eglises_actives}</div>
          <div className="stat-libelle">Églises actives</div>
        </div>
        <div className="carte">
          <div className="stat-chiffre">{stats.repartition_membres.total}</div>
          <div className="stat-libelle">Fidèles enregistrés (national)</div>
        </div>
        <div className="carte">
          <div className="stat-chiffre">{stats.nombre_religions}</div>
          <div className="stat-libelle">Religions recensées</div>
        </div>
      </div>

      {stats.finance && (
        <div className="grille-stats finance-stats national-finance-strip">
          <div className="stat-card stat-finance"><span>↗</span><strong>{Number(stats.finance.entrees).toLocaleString("fr-FR")} GNF</strong><small>Entrées réseau</small></div>
          <div className="stat-card stat-finance"><span>↘</span><strong>{Number(stats.finance.sorties).toLocaleString("fr-FR")} GNF</strong><small>Sorties réseau</small></div>
          <div className="stat-card stat-finance"><span>₣</span><strong>{Number(stats.finance.solde).toLocaleString("fr-FR")} GNF</strong><small>Solde consolidé</small></div>
          <div className="stat-card stat-finance"><span>▣</span><strong>{stats.finance.projets}</strong><small>Projets nationaux & locaux</small></div>
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
        <div className="carte">
          <h3>Répartition par sexe</h3>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie data={donneesRepartition} dataKey="valeur" nameKey="nom" outerRadius={90} label>
                {donneesRepartition.map((_, i) => <Cell key={i} fill={COULEURS[i % COULEURS.length]} />)}
              </Pie>
              <Tooltip /><Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="carte">
          <h3>Répartition par âge</h3>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie data={donneesAge} dataKey="valeur" nameKey="nom" outerRadius={90} label>
                {donneesAge.map((_, i) => <Cell key={i} fill={COULEURS[(i + 2) % COULEURS.length]} />)}
              </Pie>
              <Tooltip /><Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="carte">
          <h3>Nombre d'églises par région</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={stats.eglises_par_region}>
              <XAxis dataKey="region__nom" hide />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="nb_eglises" fill="#1a3c5e" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="carte">
          <h3>Top 20 — Membres par église</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={stats.membres_par_eglise_top20} layout="vertical">
              <XAxis type="number" allowDecimals={false} />
              <YAxis type="category" dataKey="eglise__nom" width={140} tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="nb" fill="#c9a227" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="carte">
        <h3>Bureau national actuel</h3>
        <table>
          <thead><tr><th>Nom</th><th>Fonction</th><th>Rôle</th></tr></thead>
          <tbody>
            {stats.bureau_national.map((m) => (
              <tr key={m.id}><td>{m.prenom} {m.nom}</td><td>{m.fonction_bureau_national || "-"}</td><td>{m.role}</td></tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
