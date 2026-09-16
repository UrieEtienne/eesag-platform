import { createContext, useContext, useEffect, useMemo, useState } from "react";
import client from "../api/client";

const AuthContext=createContext(null);
const ROLES_NATIONAUX=["COORDINATEUR","SUPERADMIN_INTL","SUPERADMIN_NATIONAL"];
const ROLES_BUREAU=["SUPERADMIN_INTL","SUPERADMIN_NATIONAL"];
const ROLES_GESTION_EGLISE=["ADMIN_LOCAL","PASTEUR"];

export function AuthProvider({children}){
  const [utilisateur,setUtilisateur]=useState(null);
  const [bureaux,setBureaux]=useState([]);
  const [chargement,setChargement]=useState(true);

  const chargerContexte=async()=>{
    try{ const r=await client.get("/bureaux/mes-bureaux/"); setBureaux(r.data?.results||r.data||[]); }
    catch{ setBureaux([]); }
  };

  useEffect(()=>{
    const token=localStorage.getItem("access_token");
    if(!token){setChargement(false);return;}
    client.get("/auth/moi/").then(async r=>{setUtilisateur(r.data);await chargerContexte();}).catch(()=>{localStorage.clear();setUtilisateur(null);setBureaux([]);}).finally(()=>setChargement(false));
  },[]);

  const connecter=async(identifiant,password)=>{
    const {data}=await client.post("/auth/login/",{identifiant,password});
    localStorage.setItem("access_token",data.access);localStorage.setItem("refresh_token",data.refresh);
    setUtilisateur(data.utilisateur);await chargerContexte();return data.utilisateur;
  };
  const deconnecter=()=>{localStorage.clear();setUtilisateur(null);setBureaux([]);};

  const value=useMemo(()=>{
    const estCoordinateur=Boolean(utilisateur?.role==="COORDINATEUR"||utilisateur?.is_superuser);
    const estBureauNational=Boolean(utilisateur&&ROLES_BUREAU.includes(utilisateur.role));
    const estBureauNationalGeneral=Boolean(estBureauNational && bureaux.length===0);
    const estGestionnaireEglise=Boolean(utilisateur&&ROLES_GESTION_EGLISE.includes(utilisateur.role));
    const estMembre=utilisateur?.role==="MEMBRE";
    const peutGerer=estCoordinateur||estBureauNationalGeneral||estGestionnaireEglise||estBureauNational;
    return {utilisateur,bureaux,connecter,deconnecter,chargement,estNational:utilisateur?ROLES_NATIONAUX.includes(utilisateur.role):false,estCoordinateur,estBureauNational,estBureauNationalGeneral,estGestionnaireEglise,estMembre,peutGerer};
  },[utilisateur,bureaux,chargement]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
export const useAuth=()=>useContext(AuthContext);
