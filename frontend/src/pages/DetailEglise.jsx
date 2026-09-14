import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";
import client from "../api/client";
import { useAuth } from "../context/AuthContext";
import FormulaireMembre from "../components/FormulaireMembre";
import FormulaireAffectationPasteur from "../components/FormulaireAffectationPasteur";

const COULEURS = ["#1a3c5e", "#c9a227", "#2e7d32", "#c0392b"];

export default function DetailEglise() {
  const { id } = useParams();
  const [eglise, setEglise] = useState(null);
  const [stats, setStats] = useState(null);
  const [membres, setMembres] = useState([]);
  const [ongletActif, setOngletActif] = useState("apercu");
  const [afficherAjoutMembre, setAfficherAjoutMembre] = useState(false);
  const [afficherAffectation, setAfficherAffectation] = useState(false);
  const { estNational, utilisateur } = useAuth();

  const peutGererCetteEglise = estNational || utilisateur?.eglise === Number(id);

  const charger = () => {
    client.get(`/eglises/${id}/`).then((res) => setEglise(res.data));
    client.get(`/stats/eglise/${id}/`).then((res) => setStats(res.data));
    client.get("/utilisateurs/", { params: { eglise: id } }).then((res) => setMembres(res.data.results || res.data));
  };

  useEffect(charger, [id]);

  if (!eglise) return <p>Chargement...</p>;

  const donneesSexe = stats ? [
    { nom: "Hommes", valeur: stats.repartition_membres.hommes },
    { nom: "Femmes", valeur: stats.repartition_membres.femmes },
  ] : [];

  return (
    <div>
      <div className="barre-superieure">
        <h2>{eglise.nom} <small style={{ color: "#888" }}>({eglise.code})</small></h2>
        {peutGererCetteEglise && (
          <div style={{ display: "flex", gap: 8 }}>
            <button className="btn btn-secondaire" onClick={() => setAfficherAjoutMembre(true)}>+ Ajouter un membre</button>
            {estNational && (
              <button className="btn" onClick={() => setAfficherAffectation(true)}>Affecter un pasteur</button>
            )}
          </div>
        )}
      </div>

      <div className="carte">
        <p><b>Religion :</b> {eglise.religion_nom} &nbsp;|&nbsp; <b>Statut :</b> {eglise.statut}</p>
        <p><b>Localisation :</b> {eglise.region_nom} &gt; {eglise.prefecture_nom} &gt; {eglise.district_nom} {eglise.commune_nom ? `> ${eglise.commune_nom}` : ""}</p>
        <p><b>Adresse :</b> {eglise.adresse_precise || "—"} &nbsp;|&nbsp; <b>Téléphone :</b> {eglise.telephone || "—"}</p>
        <p><b>Responsable actuel :</b> {eglise.responsable_nom || "Aucun pasteur affecté"}</p>
      </div>

      <div style={{ display: "flex", gap: 10, marginBottom: 16 }}>
        {["apercu", "membres", "departements"].map((o) => (
          <button key={o} className={`btn ${ongletActif === o ? "" : "btn-secondaire"}`} onClick={() => setOngletActif(o)}>
            {o === "apercu" ? "Tableau de bord" : o === "membres" ? "Membres" : "Départements"}
          </button>
        ))}
      </div>

      {ongletActif === "apercu" && stats && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
          <div className="grille-stats" style={{ gridColumn: "1 / -1" }}>
            <div className="carte"><div className="stat-chiffre">{stats.repartition_membres.total}</div><div className="stat-libelle">Total fidèles</div></div>
            <div className="carte"><div className="stat-chiffre">{stats.repartition_membres.enfants}</div><div className="stat-libelle">Enfants</div></div>
            <div className="carte"><div className="stat-chiffre">{stats.repartition_membres.jeunes}</div><div className="stat-libelle">Jeunes</div></div>
            <div className="carte"><div className="stat-chiffre">{stats.repartition_membres.adultes}</div><div className="stat-libelle">Adultes</div></div>
            <div className="carte"><div className="stat-chiffre">{stats.nombre_departements}</div><div className="stat-libelle">Départements</div></div>
          </div>
          <div className="carte">
            <h3>Répartition par sexe</h3>
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie data={donneesSexe} dataKey="valeur" nameKey="nom" outerRadius={80} label>
                  {donneesSexe.map((_, i) => <Cell key={i} fill={COULEURS[i]} />)}
                </Pie>
                <Tooltip /><Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {ongletActif === "membres" && (
        <div className="carte">
          <table>
            <thead><tr><th>Identifiant</th><th>Nom</th><th>Sexe</th><th>Rôle</th><th>Département</th><th>Téléphone</th></tr></thead>
            <tbody>
              {membres.map((m) => (
                <tr key={m.id}>
                  <td>{m.identifiant}</td><td>{m.nom_complet}</td><td>{m.sexe}</td>
                  <td>{m.role_libelle}</td><td>{m.departement || "—"}</td><td>{m.telephone}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {ongletActif === "departements" && (
        <div className="carte">
          <table>
            <thead><tr><th>Nom</th><th>Responsable</th><th>Membres</th></tr></thead>
            <tbody>
              {eglise.departements?.map((d) => (
                <tr key={d.id}><td>{d.nom}</td><td>{d.responsable_nom || "—"}</td><td>{d.nombre_membres}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {afficherAjoutMembre && (
        <FormulaireMembre
          egliseId={id}
          onFerme={() => setAfficherAjoutMembre(false)}
          onCree={() => { setAfficherAjoutMembre(false); charger(); }}
        />
      )}
      {afficherAffectation && (
        <FormulaireAffectationPasteur
          egliseId={id}
          onFerme={() => setAfficherAffectation(false)}
          onAffecte={() => { setAfficherAffectation(false); charger(); }}
        />
      )}
    </div>
  );
}
