import { Routes, Route } from "react-router-dom";
import RouteProtegee from "./components/RouteProtegee";
import Connexion from "./pages/Connexion";
import Inscription from "./pages/Inscription";
import Profil from "./pages/Profil";
import GestionAdministrateurs from "./pages/GestionAdministrateurs";
import Rapports from "./pages/Rapports";
import Membres from "./pages/Membres";
import Accueil from "./pages/Accueil";
import TableauDeBordNational from "./pages/TableauDeBordNational";
import ListeEglises from "./pages/ListeEglises";
import DetailEglise from "./pages/DetailEglise";
import RechercheMembre from "./pages/RechercheMembre";
import BureauNational from "./pages/BureauNational";
import Courriers from "./pages/Courriers";
import Documents from "./pages/Documents";
import Notifications from "./pages/Notifications";
import Finances from "./pages/Finances";
import Geographie from "./pages/Geographie";
import Annexes from "./pages/Annexes";
import AssistantIA from "./pages/AssistantIA";
import Reunions from "./pages/Reunions";
import Parametres from "./pages/Parametres";
import Bureaux from "./pages/Bureaux";
import Informations from "./pages/Informations";
import Systeme from "./pages/Systeme";
import EspaceAccueil from "./pages/EspaceAccueil";
import Departements from "./pages/Departements";
import TableauDeBordEglise from "./pages/TableauDeBordEglise";
import Layout from "./components/Layout";

export default function App(){
  const protect=(element, props={})=>(
    <RouteProtegee {...props}>
      <Layout>{element}</Layout>
    </RouteProtegee>
  );

  return <Routes>
    <Route path="/connexion" element={<Connexion/>}/>
    <Route path="/inscription" element={<Inscription/>}/>

    <Route path="/" element={protect(<EspaceAccueil/>)}/>
    <Route path="/eglise-dashboard" element={protect(<TableauDeBordEglise/>, {roles:["ADMIN_LOCAL","PASTEUR"]})}/>
    <Route path="/national" element={protect(<TableauDeBordNational/>, {roles:["COORDINATEUR"]})}/>
    <Route path="/eglises" element={protect(<ListeEglises/>, {roles:["COORDINATEUR","SUPERADMIN_INTL","SUPERADMIN_NATIONAL"], feature:"eglises"})}/>
    <Route path="/eglises/:id" element={protect(<DetailEglise/>)}/>
    <Route path="/bureaux" element={protect(<Bureaux/>, {feature:"bureaux"})}/>
    <Route path="/bureau-national" element={protect(<BureauNational/>)}/>
    <Route path="/membres" element={protect(<Membres/>, {roles:["COORDINATEUR","ADMIN_LOCAL","PASTEUR"], feature:"membres"})}/>
    <Route path="/departements" element={protect(<Departements/>, {roles:["COORDINATEUR","ADMIN_LOCAL","PASTEUR"], feature:"departements"})}/>
    <Route path="/administrateurs" element={protect(<GestionAdministrateurs/>, {roles:["COORDINATEUR","SUPERADMIN_NATIONAL","ADMIN_LOCAL","PASTEUR"], feature:"administrateurs_eglises"})}/>
    <Route path="/documents" element={protect(<Documents/>, {feature:"documents"})}/>
    <Route path="/notifications" element={protect(<Notifications/>, {feature:"notifications"})}/>
    <Route path="/finances" element={protect(<Finances/>, {feature:"finances"})}/>
    <Route path="/annexes" element={protect(<Annexes/>, {feature:"annexes"})}/>
    <Route path="/rapports" element={protect(<Rapports/>, {feature:"rapports"})}/>
    <Route path="/reunions" element={protect(<Reunions/>, {feature:"reunions"})}/>
    <Route path="/ia" element={protect(<AssistantIA/>, {feature:"assistant_ia"})}/>
    <Route path="/courriers" element={protect(<Courriers/>, {feature:"courriers"})}/>
    <Route path="/recherche" element={protect(<RechercheMembre/>)}/>
    <Route path="/geographie" element={protect(<Geographie/>)}/>
    <Route path="/profil" element={protect(<Profil/>)}/>
    <Route path="/parametres" element={protect(<Parametres/>, {roles:["COORDINATEUR"]})}/>
    <Route path="/informations" element={protect(<Informations/>)}/>
    <Route path="/systeme" element={protect(<Systeme/>, {roles:["COORDINATEUR","SUPERADMIN_INTL","SUPERADMIN_NATIONAL","ADMIN_LOCAL","PASTEUR"]})}/>
  </Routes>
}
