import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import client from "../api/client";
import { useAuth } from "../context/AuthContext";
import FormulaireEglise from "../components/FormulaireEglise";

export default function ListeEglises() {
  const [eglises,setEglises]=useState([]),[religions,setReligions]=useState([]),[recherche,setRecherche]=useState(""),[religionFiltre,setReligionFiltre]=useState("");
  const [afficherFormulaire,setAfficherFormulaire]=useState(false),[erreur,setErreur]=useState("");
  const {estCoordinateur,estBureauNationalGeneral,estBureauNational,utilisateur}=useAuth();
  const peutAdministrer=estCoordinateur||estBureauNationalGeneral;
  const lectureSeule=estBureauNational&&!estBureauNationalGeneral;
  const charger=()=>client.get("/eglises/",{params:{...(recherche?{search:recherche}:{}),...(religionFiltre?{religion:religionFiltre}:{})}}).then(r=>setEglises(r.data.results||r.data||[])).catch(e=>setErreur(e.response?.data?.detail||"Impossible de charger l’annuaire."));
  useEffect(()=>{client.get("/religions/").then(r=>setReligions(r.data.results||r.data||[])).catch(()=>setReligions([]));},[]);
  useEffect(()=>{const t=setTimeout(charger,250);return()=>clearTimeout(t)},[recherche,religionFiltre]);
  return <div><div className="page-hero"><div><span className="eyebrow">ANNUAIRE & CONTRÔLE</span><h1>Églises & activation</h1><p>Les informations générales sont visibles selon le périmètre. L’activation de la plateforme est exclusivement gérée dans Django admin par le Bureau national.</p></div>{peutAdministrer&&<button className="btn" onClick={()=>setAfficherFormulaire(true)}>+ Créer une église</button>}</div>
    {lectureSeule&&<div className="console-note">Votre bureau national spécialisé dispose uniquement de l’annuaire. Il ne peut ni ajouter des membres d’église, ni gérer les départements, ni administrer les comptes des églises.</div>}
    {erreur&&<div className="console-error">{erreur}</div>}
    <div className="filtres"><input placeholder="Rechercher une église…" value={recherche} onChange={e=>setRecherche(e.target.value)}/><select value={religionFiltre} onChange={e=>setReligionFiltre(e.target.value)}><option value="">Toutes les religions</option>{religions.map(r=><option key={r.id} value={r.id}>{r.nom}</option>)}</select></div>
    <div className="carte table-wrap"><table><thead><tr><th>Code</th><th>Église</th><th>Religion</th><th>Région</th><th>Statut plateforme</th>{peutAdministrer&&<th>Membres</th>}<th></th></tr></thead><tbody>{eglises.map(e=><tr key={e.id}><td><b>{e.code}</b></td><td>{e.nom}</td><td>{e.religion_nom}</td><td>{e.region_nom}</td><td>{e.plateforme_active?<span className="status-active">Active</span>:<span className="status-off">À activer</span>}</td>{peutAdministrer&&<td>{e.nombre_membres??"—"}</td>}<td>{peutAdministrer||utilisateur?.eglise===e.id?<Link className="btn btn-petit btn-secondaire" to={`/eglises/${e.id}`}>Ouvrir</Link>:<span className="tag">Annuaire</span>}</td></tr>)}{eglises.length===0&&<tr><td colSpan={peutAdministrer?7:6}><div className="empty-state">Aucune église trouvée.</div></td></tr>}</tbody></table></div>
    {afficherFormulaire&&<FormulaireEglise onFerme={()=>setAfficherFormulaire(false)} onCree={()=>{setAfficherFormulaire(false);charger()}}/>}
  </div>;
}
