import { useState } from "react";
import client from "../api/client";
import { useAuth } from "../context/AuthContext";

export default function Rapports() {
  const { utilisateur } = useAuth();
  const [form, setForm] = useState({ periode: "annee", debut: "", fin: "", membres: true, finances: true, projets: true });
  const [preview, setPreview] = useState(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  const params = () => {
    const p = new URLSearchParams({ periode: form.periode, membres: form.membres ? "1" : "0", finances: form.finances ? "1" : "0", projets: form.projets ? "1" : "0" });
    if (form.debut) p.set("debut", form.debut); if (form.fin) p.set("fin", form.fin); return p;
  };

  const apercu = async () => { setErr(""); setBusy(true); try { const r = await client.get(`/stats/rapport-apercu/?${params()}`); setPreview(r.data); } catch (e) { setErr(e.response?.data?.detail || "Aperçu impossible."); } finally { setBusy(false); } };

  const exporter = async () => {
    if (!preview) return;
    setBusy(true); setErr("");
    try {
      let path = "/stats/rapport-national/";
      if (preview.scope.type === "EGLISE") path = `/stats/rapport/${preview.scope.eglise_id}/`;
      if (preview.scope.type === "BUREAU") path = `/stats/rapport-bureau/${preview.scope.bureau_id}/`;
      const r = await client.get(`${path}?${params()}`, { responseType: "blob" });
      const url = URL.createObjectURL(r.data); const a = document.createElement("a"); a.href = url; a.download = `rapport-${preview.label.replace(/\s+/g, "-")}.pdf`; a.click(); URL.revokeObjectURL(url);
    } catch (e) { setErr(e.response?.data?.detail || "Export impossible."); } finally { setBusy(false); }
  };

  return <div className="reports-page"><div className="page-hero reports-hero"><div><span className="eyebrow">RAPPORTS · APERÇU · EXPORT</span><h1>Rapports de ma structure</h1><p>Chaque structure produit uniquement son propre rapport. L’aperçu est obligatoire avant l’export.</p></div><div className="finance-hero-badge">{preview?.label || utilisateur?.eglise_nom || "Mon périmètre"}</div></div>{err && <div className="console-error">{err}</div>}
    <section className="carte report-builder"><div className="section-header"><div><span className="eyebrow">PERSONNALISATION</span><h3>Période et rubriques</h3></div><span className="scope-badge">Périmètre verrouillé</span></div>
      <div className="report-periods">{[["semaine","Semaine"],["mois","Mois"],["annee","Année"],["personnalisee","Personnalisée"]].map(([v,l]) => <button key={v} className={form.periode===v?"selected":""} onClick={() => setForm({...form, periode:v})}>{l}</button>)}</div>
      {form.periode === "personnalisee" && <div className="form-row"><div className="form-champ"><label>Du</label><input type="date" value={form.debut} onChange={(e)=>setForm({...form,debut:e.target.value})}/></div><div className="form-champ"><label>Au</label><input type="date" value={form.fin} onChange={(e)=>setForm({...form,fin:e.target.value})}/></div></div>}
      <div className="report-checks"><label><input type="checkbox" checked={form.membres} onChange={(e)=>setForm({...form,membres:e.target.checked})}/> Membres & démographie</label><label><input type="checkbox" checked={form.finances} onChange={(e)=>setForm({...form,finances:e.target.checked})}/> Comptabilité détaillée</label><label><input type="checkbox" checked={form.projets} onChange={(e)=>setForm({...form,projets:e.target.checked})}/> Projets & budgets</label></div>
      <div className="report-actions"><button className="btn" onClick={apercu} disabled={busy}>{busy ? "Préparation…" : "Afficher l’aperçu"}</button>{preview && <button className="btn" onClick={exporter} disabled={busy}>Exporter après validation</button>}<button className="btn btn-secondaire" onClick={()=>window.print()}>Imprimer</button></div>
    </section>
    {preview && <section className="carte report-preview-card"><div className="section-header"><div><span className="eyebrow">APERÇU DU RAPPORT</span><h3>{preview.label}</h3></div><span>{preview.periode.debut} → {preview.periode.fin}</span></div><div className="report-preview-grid">{preview.membres && <div><b>{preview.membres.total}</b><small>Membres actifs</small><span>{preview.membres.hommes} hommes · {preview.membres.femmes} femmes</span></div>}{preview.finances && <div><b>{Number(preview.finances.solde||0).toLocaleString("fr-FR")} GNF</b><small>Solde</small><span>{Number(preview.finances.entrees||0).toLocaleString("fr-FR")} entrées · {Number(preview.finances.sorties||0).toLocaleString("fr-FR")} sorties</span></div>}{preview.projets && <div><b>{preview.projets.nombre}</b><small>Projets</small><span>Budget prévu : {Number(preview.projets.budget_prevu||0).toLocaleString("fr-FR")} GNF</span></div>}</div><div className="preview-confirm">Vérifiez ces données avant l’export. Le fichier final sera généré uniquement pour <b>{preview.label}</b>.</div></section>}
  </div>;
}
