import {useEffect,useMemo,useState} from "react";
import client from "../api/client";
import {useAuth} from "../context/AuthContext";

export default function GestionAdministrateurs(){
  const {utilisateur,estCoordinateur,estBureauNationalGeneral,estGestionnaireEglise}=useAuth();
  const national=estCoordinateur||estBureauNationalGeneral;
  const [eglises,setEglises]=useState([]),[permissions,setPermissions]=useState([]),[users,setUsers]=useState([]);
  const [sel,setSel]=useState([]),[msg,setMsg]=useState(""),[erreur,setErreur]=useState("");
  const [form,setForm]=useState({nom:"",prenom:"",telephone:"",email:"",role:"ADMIN_LOCAL",eglise:""});

  const charger=async()=>{
    try{
      const requests=[client.get("/permissions-eglise/")];
      if(national) requests.push(client.get("/eglises/"));
      requests.push(client.get("/utilisateurs/?role=ADMIN_LOCAL"));
      const out=await Promise.all(requests);
      setPermissions(out[0].data.results||out[0].data||[]);
      if(national){const d=out[1].data.results||out[1].data||[];setEglises(d);setUsers(out[2].data.results||out[2].data||[]);}
      else setUsers(out[1].data.results||out[1].data||[]);
    }catch(e){setErreur(e.response?.data?.detail||"Impossible de charger les administrateurs.")}
  };
  useEffect(()=>{ if(estGestionnaireEglise||national) charger(); },[national,estGestionnaireEglise]);

  const egliseChoisie=useMemo(()=>national?form.eglise:utilisateur?.eglise,[national,form.eglise,utilisateur?.eglise]);
  const titre=national?"Administrateurs des églises":"Administrateurs de mon église";

  const create=async e=>{
    e.preventDefault();setErreur("");setMsg("");
    if(!egliseChoisie){setErreur("Sélectionnez une église.");return;}
    try{
      const r=await client.post("/utilisateurs/",{...form,eglise:Number(egliseChoisie),departement:null});
      const uid=r.data.id;
      await client.post("/delegations-eglise/",{utilisateur:uid,permissions:sel});
      setMsg(`Compte créé : ${r.data.identifiant}. Le mot de passe doit être transmis par un canal sécurisé et le compte suit le parcours de confirmation prévu.`);
      setForm({nom:"",prenom:"",telephone:"",email:"",role:"ADMIN_LOCAL",eglise:""});setSel([]);charger();
    }catch(err){setErreur(err.response?.data?.detail||JSON.stringify(err.response?.data||{}))}
  };

  if(!national&&!estGestionnaireEglise) return <div className="carte console-error"><h3>Accès non autorisé</h3><p>Les administrateurs d’églises ne sont pas accessibles à ce périmètre.</p></div>;

  return <div>
    <div className="page-hero"><div><span className="eyebrow">{national?"PILOTAGE NATIONAL":"GESTION LOCALE"}</span><h1>{titre}</h1><p>{national?"Le Bureau national général crée et supervise les comptes administrateurs des églises. Un bureau national spécialisé n’a pas accès à cette fonction.":"Le pasteur ou l’administrateur local peut déléguer des fonctions précises dans sa propre église."}</p></div></div>
    {msg&&<div className="console-success">{msg}</div>}{erreur&&<div className="console-error">{erreur}</div>}
    <div className="dashboard-grid">
      <section className="carte"><h3>Créer un administrateur local</h3><form onSubmit={create}>
        {national&&<div className="form-champ"><label>Église *</label><select value={form.eglise} onChange={e=>setForm({...form,eglise:e.target.value})} required><option value="">Choisir une église</option>{eglises.map(e=><option key={e.id} value={e.id}>{e.nom} · {e.code}</option>)}</select></div>}
        <div className="form-grid"><div className="form-champ"><label>Nom *</label><input value={form.nom} onChange={e=>setForm({...form,nom:e.target.value})} required/></div><div className="form-champ"><label>Prénom *</label><input value={form.prenom} onChange={e=>setForm({...form,prenom:e.target.value})} required/></div><div className="form-champ"><label>Téléphone *</label><input inputMode="tel" value={form.telephone} onChange={e=>setForm({...form,telephone:e.target.value})} required/></div><div className="form-champ"><label>Email</label><input type="email" value={form.email} onChange={e=>setForm({...form,email:e.target.value})}/></div></div>
        <h4>Permissions déléguées</h4><div className="selection-grid">{permissions.map(p=><label className={`selection-card ${sel.includes(p.id)?"selected":""}`} key={p.id}><input type="checkbox" checked={sel.includes(p.id)} onChange={()=>setSel(sel.includes(p.id)?sel.filter(x=>x!==p.id):[...sel,p.id])}/><span><b>{p.libelle}</b><small>{p.description}</small></span></label>)}</div>
        <button className="btn">Créer l’administrateur</button>
      </form></section>
      <section className="carte"><h3>Administrateurs existants</h3><div className="table-wrap"><table><thead><tr>{national&&<th>Église</th>}<th>Identifiant</th><th>Nom</th><th>Téléphone</th><th>État</th></tr></thead><tbody>{users.map(u=><tr key={u.id}>{national&&<td>{u.eglise_nom||"—"}</td>}<td><b>{u.identifiant}</b></td><td>{u.prenom} {u.nom}</td><td>{u.telephone}</td><td>{u.actif?<span className="status-active">Actif</span>:<span className="status-off">En attente</span>}</td></tr>)}</tbody></table></div></section>
    </div></div>;
}
