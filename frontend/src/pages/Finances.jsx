import { useEffect, useState } from "react";
import client from "../api/client";
import { useAuth } from "../context/AuthContext";

const money = (v) => `${Number(v || 0).toLocaleString("fr-FR")} GNF`;

export default function Finances() {
  const { utilisateur } = useAuth();
  const [resume, setResume] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [projets, setProjets] = useState([]);
  const [afficherForm, setAfficherForm] = useState(false);
  const [erreur, setErreur] = useState("");
  const [chargement, setChargement] = useState(true);

  const charger = () => {
    setChargement(true);
    Promise.all([
      client.get("/finance/transactions/resume/"),
      client.get("/finance/transactions/"),
      client.get("/finance/projets/"),
    ])
      .then(([r, t, p]) => {
        setResume(r.data);
        setTransactions(t.data.results || t.data);
        setProjets(p.data.results || p.data);
      })
      .catch((err) => setErreur(err.response?.data?.detail || "Impossible de charger votre comptabilité."))
      .finally(() => setChargement(false));
  };

  useEffect(charger, []);

  const labelPerimetre = () => {
    if (resume?.perimetre?.type === "GLOBAL") return "Réseau EESAG · Coordinateur";
    if (resume?.perimetre?.type === "BUREAU") return `Bureau · ${resume.perimetre.bureau_nom || "mon bureau"}`;
    if (resume?.perimetre?.type === "NATIONAL") return "Bureau national";
    return utilisateur?.eglise_nom || "Mon église";
  };

  const exporter = async () => {
    try {
      const params = "?periode=annee&membres=1&finances=1&projets=1";
      let path = "/stats/rapport-national/";
      if (resume?.perimetre?.type === "EGLISE") path = `/stats/rapport/${resume.perimetre.eglise_id}/`;
      if (resume?.perimetre?.type === "BUREAU") path = `/stats/rapport-bureau/${resume.perimetre.bureau_id}/`;
      const r = await client.get(`${path}${params}`, { responseType: "blob" });
      const url = URL.createObjectURL(r.data); const a = document.createElement("a"); a.href = url; a.download = "rapport-financier-eesag.pdf"; a.click(); URL.revokeObjectURL(url);
    } catch (err) { setErreur(err.response?.data?.detail || "Le rapport financier n’est pas disponible."); }
  };

  return (
    <div className="finance-page">
      <div className="page-hero finance-hero">
        <div>
          <span className="eyebrow">FINANCES · COMPTABILITÉ · PROJETS</span>
          <h1>Centre financier</h1>
          <p>Vous travaillez uniquement dans votre propre périmètre comptable. Aucun autre bureau ou église ne peut être sélectionné ici.</p>
        </div>
        <div className="finance-hero-badge">{labelPerimetre()}</div>
      </div>

      {erreur && <div className="console-error">{erreur}</div>}

      <div className="finance-locked-scope">
        <span>🔒</span>
        <div><b>Périmètre verrouillé</b><small>Les opérations sont automatiquement rattachées à votre église ou à votre bureau. Le serveur refuse tout changement de périmètre.</small></div>
      </div>

      <div className="grille-stats finance-stats">
        <div className="stat-card stat-finance"><span>↗</span><strong>{money(resume?.total_entrees)}</strong><small>Total des entrées</small></div>
        <div className="stat-card stat-finance"><span>↘</span><strong>{money(resume?.total_sorties)}</strong><small>Total des sorties</small></div>
        <div className="stat-card stat-finance"><span>₣</span><strong>{money(resume?.solde)}</strong><small>Solde disponible</small></div>
        <div className="stat-card stat-finance"><span>▣</span><strong>{transactions.length}</strong><small>Opérations affichées</small></div>
      </div>

      <div className="finance-grid">
        <section className="carte finance-panel">
          <div className="section-header"><div><span className="eyebrow">JOURNAL DE MA STRUCTURE</span><h3>Transactions récentes</h3></div><button className="btn" onClick={() => setAfficherForm(true)}>+ Nouvelle opération</button></div>
          <div className="table-responsive">
            <table><thead><tr><th>Date</th><th>Type</th><th>Montant</th><th>Description</th><th>Périmètre</th></tr></thead>
              <tbody>
                {chargement && <tr><td colSpan={5} className="empty-cell">Chargement…</td></tr>}
                {!chargement && transactions.slice(0, 30).map((t) => <tr key={t.id}><td>{t.date_transaction}</td><td><span className="tag-finance">{t.type_transaction}</span></td><td><b>{money(t.montant)}</b></td><td>{t.description || "—"}</td><td>{t.bureau_nom || t.eglise_nom || labelPerimetre()}</td></tr>)}
                {!chargement && !transactions.length && <tr><td colSpan={5} className="empty-cell">Aucune opération pour votre structure.</td></tr>}
              </tbody>
            </table>
          </div>
        </section>

        <section className="carte finance-panel">
          <div className="section-header"><div><span className="eyebrow">PROJETS</span><h3>Projets de ma structure</h3></div><span className="panel-chip">{projets.length}</span></div>
          {projets.map((p) => <div className="project-row" key={p.id}><div><b>{p.nom}</b><small>{p.statut} · Budget {money(p.budget_prevu)}</small></div><div className="project-money"><b>{money(p.budget_utilise)}</b><small>utilisé</small></div></div>)}
          {!projets.length && <div className="empty-state">Aucun projet pour votre structure.</div>}
        </section>
      </div>

      <div className="finance-footer-actions"><button className="btn" onClick={exporter}>Exporter le rapport PDF</button><button className="btn btn-secondaire" onClick={() => window.print()}>Imprimer</button></div>
      {afficherForm && <FormulaireTransaction onFerme={() => setAfficherForm(false)} onCree={() => { setAfficherForm(false); charger(); }} />}
    </div>
  );
}

function FormulaireTransaction({ onFerme, onCree }) {
  const [form, setForm] = useState({ type_transaction: "DIME", montant: "", description: "", date_transaction: new Date().toISOString().slice(0, 10) });
  const [saving, setSaving] = useState(false); const [erreur, setErreur] = useState("");
  const modifier = (c, v) => setForm((f) => ({ ...f, [c]: v }));
  const soumettre = async (e) => { e.preventDefault(); setSaving(true); setErreur(""); try { await client.post("/finance/transactions/", form); onCree(); } catch (err) { setErreur(err.response?.data?.detail || "Opération refusée."); } finally { setSaving(false); } };
  return <div className="modale-fond" onClick={onFerme}><div className="modale" onClick={(e) => e.stopPropagation()}><div className="modal-head"><div><span className="eyebrow">PÉRIMÈTRE AUTOMATIQUE</span><h3>Nouvelle opération</h3></div><button className="modal-close" onClick={onFerme}>×</button></div><form onSubmit={soumettre}>{erreur && <p className="erreur">{erreur}</p>}<div className="form-champ"><label>Type *</label><select value={form.type_transaction} onChange={(e) => modifier("type_transaction", e.target.value)}><option value="DIME">Dîme</option><option value="OFFRANDE">Offrande</option><option value="DON">Don</option><option value="AUTRE_ENTREE">Autre entrée</option><option value="SORTIE">Sortie / Dépense</option></select></div><div className="form-row"><div className="form-champ"><label>Montant (GNF) *</label><input required min="0" type="number" value={form.montant} onChange={(e) => modifier("montant", e.target.value)} /></div><div className="form-champ"><label>Date *</label><input required type="date" value={form.date_transaction} onChange={(e) => modifier("date_transaction", e.target.value)} /></div></div><div className="form-champ"><label>Description</label><textarea rows="4" value={form.description} onChange={(e) => modifier("description", e.target.value)} /></div><div className="modal-actions"><button type="button" className="btn btn-secondaire" onClick={onFerme}>Annuler</button><button className="btn" disabled={saving}>{saving ? "Enregistrement…" : "Enregistrer"}</button></div></form></div></div>;
}
