import { useEffect, useState } from "react";
import client from "../api/client";
import { useAuth } from "../context/AuthContext";

export default function Annexes() {
  const { peutGerer } = useAuth();
  const [annexes, setAnnexes] = useState([]);
  const [afficher, setAfficher] = useState(false);
  const [form, setForm] = useState({ nom: "", adresse: "", telephone: "", date_creation: "" });
  const [erreur, setErreur] = useState("");
  const charger = () => client.get("/annexes/").then((r) => setAnnexes(r.data.results || r.data));
  useEffect(charger, []);
  const soumettre = async (e) => { e.preventDefault(); setErreur(""); try { await client.post("/annexes/", form); setAfficher(false); setForm({ nom: "", adresse: "", telephone: "", date_creation: "" }); charger(); } catch (err) { setErreur("Impossible de créer l'annexe."); } };
  return <div><div className="barre-superieure"><div><h2>Annexes</h2><p className="sous-titre">Implantations rattachées à votre église et gérées dans votre espace privé.</p></div>{peutGerer && <button className="btn" onClick={() => setAfficher(true)}>＋ Nouvelle annexe</button>}</div><div className="cards-list">{annexes.map((a) => <div className="carte card-compact" key={a.id}><div className="code-pill">{a.code}</div><h3>{a.nom}</h3><p>{a.adresse || "Adresse non renseignée"}</p><small>{a.telephone || "Téléphone non renseigné"}</small><div className="card-footer"><span className={a.active ? "status-active" : "status-off"}>{a.active ? "Active" : "Inactive"}</span><span>{a.responsable_nom || "Sans responsable"}</span></div></div>)}{!annexes.length && <div className="carte"><div className="empty-state">Aucune annexe enregistrée.</div></div>}</div>{afficher && <div className="modale-fond" onClick={() => setAfficher(false)}><div className="modale" onClick={(e) => e.stopPropagation()}><h3>Nouvelle annexe</h3><form onSubmit={soumettre}><div className="form-champ"><label>Nom *</label><input required value={form.nom} onChange={(e) => setForm({...form, nom:e.target.value})} /></div><div className="form-champ"><label>Adresse</label><input value={form.adresse} onChange={(e) => setForm({...form, adresse:e.target.value})} /></div><div className="form-champ"><label>Téléphone</label><input value={form.telephone} onChange={(e) => setForm({...form, telephone:e.target.value})} /></div><div className="form-champ"><label>Date de création</label><input type="date" value={form.date_creation} onChange={(e) => setForm({...form, date_creation:e.target.value})} /></div>{erreur && <p className="erreur">{erreur}</p>}<div className="modal-actions"><button className="btn">Enregistrer</button><button type="button" className="btn btn-secondaire" onClick={() => setAfficher(false)}>Annuler</button></div></form></div></div>}</div>;
}
