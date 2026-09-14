import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

const defaults = { accent: "#d6ad3f", mode: "light", brightness: 100, font: 100 };

export default function Parametres() {
  const [prefs, setPrefs] = useState(() => { try { return { ...defaults, ...JSON.parse(localStorage.getItem("eesag_preferences") || "{}")} } catch { return defaults; }});
  useEffect(() => {
    localStorage.setItem("eesag_preferences", JSON.stringify(prefs));
    document.documentElement.style.setProperty("--eesag-accent", prefs.accent);
    document.documentElement.style.setProperty("--eesag-brightness", `${prefs.brightness}%`);
    document.documentElement.style.setProperty("--eesag-font-scale", `${prefs.font / 100}`);
    document.documentElement.dataset.theme = prefs.mode;
  }, [prefs]);
  const set = (key, value) => setPrefs((p) => ({ ...p, [key]: value }));
  return <div className="settings-page">
    <div className="page-hero settings-hero"><div><span className="eyebrow">PROPRIÉTAIRE DU SYSTÈME</span><h1>Paramètres EESAG</h1><p>Personnalisez l'apparence, la luminosité et les réglages du centre de contrôle.</p></div><span className="settings-owner-badge">COORDINATEUR</span></div>
    <div className="settings-grid">
      <section className="carte settings-card"><h3>Apparence</h3><label className="settings-label">Couleur principale</label><div className="accent-options">{[["#d6ad3f","Or institutionnel"],["#1f8fc4","Bleu réseau"],["#e85772","Corail EESAG"],["#20a477","Vert sécurité"]].map(([c,n]) => <button key={c} className={`accent-choice ${prefs.accent===c?"selected":""}`} style={{ background:c }} onClick={()=>set("accent",c)} aria-label={n}><span>{prefs.accent===c?"✓":""}</span></button>)}</div><div className="settings-value">Mode : <b>{prefs.mode === "dark" ? "Sombre" : "Clair"}</b></div><div className="segmented"><button className={prefs.mode==="light"?"selected":""} onClick={()=>set("mode","light")}>Clair</button><button className={prefs.mode==="dark"?"selected":""} onClick={()=>set("mode","dark")}>Sombre</button></div>
      </section>
      <section className="carte settings-card"><h3>Confort de lecture</h3><label className="settings-label">Luminosité : <b>{prefs.brightness}%</b></label><input type="range" min="75" max="120" value={prefs.brightness} onChange={e=>set("brightness", Number(e.target.value))}/><label className="settings-label">Taille des polices : <b>{prefs.font}%</b></label><input type="range" min="90" max="125" value={prefs.font} onChange={e=>set("font", Number(e.target.value))}/><p className="settings-preview">Aperçu EESAG — Texte de lecture, tableaux, boutons et indicateurs.</p></section>
      <section className="carte settings-card"><h3>Compte propriétaire</h3><p>Votre compte Coordinateur n'est jamais affiché dans la liste générale des utilisateurs. Gérez vos informations directement.</p><Link className="btn" to="/profil">Modifier mon compte</Link></section>
      <section className="carte settings-card"><h3>Réglages opérationnels</h3><div className="settings-list"><span>✓ Sécurité des données</span><span>✓ Contrôle national complet</span><span>✓ Journalisation des actions</span><span>✓ Notifications système</span></div></section>
    </div>
  </div>;
}
