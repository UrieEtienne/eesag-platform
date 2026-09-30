import { useEffect, useState } from "react";
import client from "../api/client";
import { useAuth } from "../context/AuthContext";

export default function Departements(){
  const { utilisateur } = useAuth();
  const [items,setItems]=useState([]),[nom,setNom]=useState(""),[msg,setMsg]=useState(""),[erreur,setErreur]=useState("");
  const charger=()=>client.get("/departements/").then(r=>setItems(r.data.results||r.data||[])).catch(e=>setErreur(e.response?.data?.detail||"Impossible de charger les départements."));
  useEffect(charger,[]);
  const ajouter=async e=>{e.preventDefault();setErreur("");setMsg("");if(!nom.trim())return;try{await client.post("/departements/",{nom:nom.trim()});setNom("");setMsg("Département ajouté au référentiel.");charger()}catch(e){setErreur(e.response?.data?.detail||JSON.stringify(e.response?.data||{}))}};
  return <div><div className="page-hero"><div><span className="eyebrow">ORGANISATION LOCALE</span><h1>Départements</h1><p>Référentiel des départements utilisés par votre église. Les comptes membres restent dans le périmètre de l’église.</p></div></div>{msg&&<div className="console-success">{msg}</div>}{erreur&&<div className="console-error">{erreur}</div>}<div className="dashboard-grid"><section className="carte"><h3>Ajouter un département</h3><form onSubmit={ajouter}><div className="form-champ"><label>Nom</label><input value={nom} onChange={e=>setNom(e.target.value)} placeholder="Ex. Jeunesse" required/></div><button className="btn">Ajouter</button></form></section><section className="carte"><h3>Départements disponibles</h3><div className="table-wrap"><table><thead><tr><th>Nom</th><th>Membres actifs</th></tr></thead><tbody>{items.map(d=><tr key={d.id}><td><b>{d.nom}</b></td><td>{d.nombre_membres??0}</td></tr>)}</tbody></table></div>{!items.length&&<div className="empty-state">Aucun département enregistré.</div>}</section></div><p className="sous-titre">Connecté à : <b>{utilisateur?.eglise_nom||"votre église"}</b></p></div>;
}
