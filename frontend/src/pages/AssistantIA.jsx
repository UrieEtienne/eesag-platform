import { useState } from "react";
import client from "../api/client";
import { useAuth } from "../context/AuthContext";

export default function AssistantIA() {
  const { estNational, peutGerer } = useAuth();
  const [action, setAction] = useState("ANALYSE");
  const [sujet, setSujet] = useState("");
  const [message, setMessage] = useState("");
  const [resultat, setResultat] = useState("");
  const [fournisseur, setFournisseur] = useState("");
  const [chargement, setChargement] = useState(false);
  const [erreur, setErreur] = useState("");

  if (!peutGerer && !estNational) return null;

  const lancer = async (e) => {
    e.preventDefault();
    setChargement(true); setErreur(""); setResultat("");
    try {
      const { data } = await client.post("/ia/assistant/", { action, sujet, message });
      setResultat(data.resultat || "Aucun résultat.");
      setFournisseur(data.fournisseur || "");
    } catch (err) {
      setErreur(err.response?.data?.detail || "Impossible de contacter l'assistant IA.");
    } finally { setChargement(false); }
  };

  return <div>
    <div className="barre-superieure">
      <div><span className="eyebrow">AUTOMATISATION</span><h2>Assistant IA</h2><p className="sous-titre">Analyse, rédaction et suggestions de mise à jour avec validation humaine.</p></div>
      <span className="secure-pill">● IA sous contrôle</span>
    </div>
    <div className="ai-grid">
      <section className="carte ai-console">
        <h3>Que souhaitez-vous automatiser ?</h3>
        <form onSubmit={lancer}>
          <div className="form-champ"><label>Action</label><select value={action} onChange={e=>setAction(e.target.value)}><option value="ANALYSE">Analyser l'activité</option><option value="BROUILLON">Rédiger un message</option><option value="MISE_A_JOUR">Suggérer des mises à jour</option><option value="RAPPORT">Résumer les indicateurs</option></select></div>
          {action === "BROUILLON" && <><div className="form-champ"><label>Sujet</label><input value={sujet} onChange={e=>setSujet(e.target.value)} placeholder="Ex. Réunion mensuelle"/></div><div className="form-champ"><label>Message source</label><textarea value={message} onChange={e=>setMessage(e.target.value)} rows={5} placeholder="Donnez les éléments que l'IA doit transformer en message…"/></div></>}
          <div className="actions"><button className="btn" disabled={chargement}>{chargement ? "Analyse…" : "Lancer l'assistant"}</button></div>
        </form>
        <p className="ai-note">L'IA ne modifie pas directement les membres, finances, rôles ou transferts. Elle produit une proposition que le responsable valide.</p>
      </section>
      <section className="carte ai-result"><div className="section-header"><div><h3>Résultat</h3><p>{fournisseur ? `Fournisseur : ${fournisseur}` : "Aucune exécution"}</p></div></div>{erreur&&<p className="erreur">{erreur}</p>}{resultat?<pre className="ai-output">{resultat}</pre>:<div className="empty-state">Le résultat de l'assistant apparaîtra ici.</div>}</section>
    </div>
  </div>;
}
