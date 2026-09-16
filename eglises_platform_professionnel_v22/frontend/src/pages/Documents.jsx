import { useEffect, useState } from "react";
import client from "../api/client";
import { useAuth } from "../context/AuthContext";

export default function Documents() {
  const { estNational, utilisateur, peutGerer } = useAuth();
  const [documents, setDocuments] = useState([]);
  const [eglises, setEglises] = useState([]);
  const [recherche, setRecherche] = useState("");
  const [afficher, setAfficher] = useState(false);
  const [erreur, setErreur] = useState("");

  const charger = () => client.get("/documents/").then((r) => setDocuments(r.data.results || r.data));
  useEffect(() => { charger(); if (peutGerer) client.get("/eglises/").then((r) => setEglises(r.data.results || r.data)); }, []);

  const marquer = async (id) => { await client.post(`/documents/${id}/marquer_recu/`); charger(); };
  const filtrerEglises = eglises.filter((e) => !recherche || `${e.nom} ${e.code}`.toLowerCase().includes(recherche.toLowerCase()));

  return <div>
    <div className="barre-superieure"><div><h2>Documents</h2><p className="sous-titre">Échange sécurisé de documents entre le bureau national et les églises.</p></div>{peutGerer && <button className="btn" onClick={() => setAfficher(true)}>＋ Envoyer un document</button>}</div>
    <div className="carte table-wrap"><table><thead><tr><th>Document</th><th>Catégorie</th><th>Expéditeur</th><th>Destinataire</th><th>Réception</th><th></th></tr></thead><tbody>
      {documents.map((d) => { const recu = d.destinataires_resume?.find((x) => x.eglise === utilisateur?.eglise); return <tr key={d.id}><td><b>{d.titre}</b><small>{d.description}</small></td><td><span className="tag">{d.categorie}</span></td><td>{d.eglise_expediteur_nom || "Bureau national"}</td><td>{d.destinataires_resume?.map((x) => x.eglise_nom).join(", ")}</td><td>{recu ? (recu.compte_reception ? "Réception confirmée" : (recu.lu ? "Lu" : "Non lu")) : "—"}</td><td><div className="actions"><a className="btn btn-petit btn-secondaire" href={d.fichier} target="_blank" rel="noreferrer">Ouvrir</a>{recu && !recu.lu && <button className="btn btn-petit" onClick={() => marquer(d.id)}>Marquer reçu</button>}</div></td></tr>;
      })}
      {!documents.length && <tr><td colSpan="6"><div className="empty-state">Aucun document accessible.</div></td></tr>}
    </tbody></table></div>
    {afficher && <FormulaireDocument egliseId={utilisateur?.eglise} estNational={estNational} eglises={filtrerEglises} recherche={recherche} setRecherche={setRecherche} onFerme={() => setAfficher(false)} onCree={() => { setAfficher(false); charger(); }} erreur={erreur} setErreur={setErreur} />}
  </div>;
}

function FormulaireDocument({ egliseId, estNational, eglises, recherche, setRecherche, onFerme, onCree, erreur, setErreur }) {
  const [form, setForm] = useState({ titre: "", description: "", categorie: "OFFICIEL", fichier: null, destinataires: [] });
  const modifier = (k, v) => setForm((f) => ({ ...f, [k]: v }));
  const soumettre = async (e) => {
    e.preventDefault(); setErreur("");
    if (!form.destinataires.length || !form.fichier) return setErreur("Sélectionnez au moins une église et un fichier.");
    const data = new FormData(); data.append("titre", form.titre); data.append("description", form.description); data.append("categorie", form.categorie); data.append("fichier", form.fichier); form.destinataires.forEach((id) => data.append("destinataires", id));
    try { await client.post("/documents/", data, { headers: { "Content-Type": "multipart/form-data" } }); onCree(); } catch (err) { setErreur(err.response?.data?.detail || "Impossible d'envoyer le document."); }
  };
  return <div className="modale-fond" onClick={onFerme}><div className="modale large" onClick={(e) => e.stopPropagation()}><div className="section-header"><div><h3>Envoyer un document</h3><p>Le document sera visible uniquement dans les espaces des églises choisies.</p></div></div>
    <form onSubmit={soumettre}>
      <div className="form-grid"><div className="form-champ"><label>Titre *</label><input required value={form.titre} onChange={(e) => modifier("titre", e.target.value)} /></div><div className="form-champ"><label>Catégorie</label><select value={form.categorie} onChange={(e) => modifier("categorie", e.target.value)}><option value="OFFICIEL">Officiel</option><option value="ADMINISTRATIF">Administratif</option><option value="RAPPORT">Rapport</option><option value="PROJET">Projet</option><option value="AUTRE">Autre</option></select></div></div>
      <div className="form-champ"><label>Description</label><textarea rows="3" value={form.description} onChange={(e) => modifier("description", e.target.value)} /></div>
      <div className="form-champ"><label>Rechercher une église</label><input placeholder="Nom ou code de l'église…" value={recherche} onChange={(e) => setRecherche(e.target.value)} /></div>
      <div className="selection-grid">{eglises.map((eg) => <label className={`selection-card ${form.destinataires.includes(eg.id) ? "selected" : ""}`} key={eg.id}><input type="checkbox" checked={form.destinataires.includes(eg.id)} onChange={(e) => modifier("destinataires", e.target.checked ? [...form.destinataires, eg.id] : form.destinataires.filter((x) => x !== eg.id))} /><div><b>{eg.nom}</b><small>{eg.code} · {eg.region_nom}</small></div></label>)}</div>
      <div className="form-champ"><label>Fichier *</label><input required type="file" accept=".pdf,.doc,.docx,.xls,.xlsx,.png,.jpg,.jpeg" onChange={(e) => modifier("fichier", e.target.files?.[0] || null)} /></div>
      {erreur && <p className="erreur">{erreur}</p>}
      <div className="modal-actions"><button className="btn" type="submit">Envoyer</button><button className="btn btn-secondaire" type="button" onClick={onFerme}>Annuler</button></div>
    </form>
  </div></div>;
}
