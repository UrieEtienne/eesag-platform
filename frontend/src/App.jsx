import { Routes, Route } from "react-router-dom";
import RouteProtegee from "./components/RouteProtegee";
import Connexion from "./pages/Connexion";
import Inscription from "./pages/Inscription";
import Profil from "./pages/Profil";
import Rapports from "./pages/Rapports";
import Membres from "./pages/Membres";
import EspaceAccueil from "./pages/EspaceAccueil";
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
import Departements from "./pages/Departements";
import TableauDeBordEglise from "./pages/TableauDeBordEglise";
import GestionAdminsEglise from "./pages/GestionAdminsEglise";
import AdministrationEglises from "./pages/AdministrationEglises";
import Layout from "./components/Layout";
import AdministrationSysteme from "./pages/AdministrationSysteme";
import AdministrationUtilisateurs from "./pages/AdministrationUtilisateurs";
const NATIONAL = ["COORDINATEUR", "SUPERADMIN_INTL", "SUPERADMIN_NATIONAL"];
const BUREAU = ["SUPERADMIN_INTL", "SUPERADMIN_NATIONAL"];
const LOCAL = ["ADMIN_LOCAL", "PASTEUR"];

export default function App() {
  const protect = (element, props = {}) => (
    <RouteProtegee {...props}>
      <Layout>{element}</Layout>
    </RouteProtegee>
  );

  return (
    <Routes>
      <Route path="/connexion" element={<Connexion />} />
      <Route path="/inscription" element={<Inscription />} />
      <Route path="/" element={protect(<EspaceAccueil />)} />

      {/* ESPACE ADMIN DU COORDINATEUR */}
      <Route
        path="/admin"
        element={
          <RouteProtegee roles={["COORDINATEUR"]}>
            <AdministrationSysteme />
          </RouteProtegee>
        }
      />
      <Route
        path="/admin-utilisateurs"
        element={
          <RouteProtegee
            roles={[
              "COORDINATEUR",
              "SUPERADMIN_INTL",
              "SUPERADMIN_NATIONAL",
            ]}
          >
            <Layout>
              <AdministrationUtilisateurs />
            </Layout>
          </RouteProtegee>
        }
      />

      {/* ESPACE ÉGLISE LOCALE */}
      <Route path="/eglise-dashboard" element={protect(<TableauDeBordEglise />, { roles: LOCAL })} />
      <Route path="/membres" element={protect(<Membres />, { roles: ["COORDINATEUR", ...LOCAL] })} />
      <Route path="/departements" element={protect(<Departements />, { roles: ["COORDINATEUR", ...LOCAL] })} />
      <Route path="/annexes" element={protect(<Annexes />, { roles: ["COORDINATEUR", ...LOCAL] })} />
      <Route path="/eglise-administration" element={protect(<GestionAdminsEglise />, { roles: ["ADMIN_LOCAL"] })} />

      {/* ESPACE NATIONAL */}
      <Route path="/admin-eglises"element={protect(<AdministrationEglises />, { roles: NATIONAL })}/>
      <Route path="/national" element={protect(<TableauDeBordNational />, { roles: NATIONAL })} />
      <Route path="/eglises" element={protect(<ListeEglises />, { roles: NATIONAL })} />
      <Route path="/eglises/:id" element={protect(<DetailEglise />, { roles: NATIONAL })} />
      <Route path="/bureau-national" element={protect(<BureauNational />, { roles: NATIONAL })} />
      <Route path="/bureaux" element={protect(<Bureaux />, { roles: BUREAU })} />

      {/* MODULES */}
      <Route path="/documents" element={protect(<Documents />)} />
      <Route path="/notifications" element={protect(<Notifications />)} />
      <Route path="/finances" element={protect(<Finances />)} />
      <Route path="/rapports" element={protect(<Rapports />)} />
      <Route path="/reunions" element={protect(<Reunions />)} />
      <Route path="/ia" element={protect(<AssistantIA />)} />
      <Route path="/courriers" element={protect(<Courriers />)} />
      <Route path="/recherche" element={protect(<RechercheMembre />)} />
      <Route path="/geographie" element={protect(<Geographie />)} />
      <Route path="/profil" element={protect(<Profil />)} />
      <Route path="/informations" element={protect(<Informations />)} />

      {/* COORDINATEUR UNIQUEMENT */}
      <Route path="/parametres" element={protect(<Parametres />, { roles: ["COORDINATEUR"] })} />
      <Route path="/systeme" element={protect(<Systeme />, { roles: ["COORDINATEUR"] })} />
    </Routes>
  );
}
