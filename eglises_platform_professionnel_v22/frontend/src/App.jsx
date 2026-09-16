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

export default function App() {
  return <Routes>
    <Route path="/connexion" element={<Connexion />} />
    <Route path="/inscription" element={<Inscription />} />
    <Route path="/" element={<RouteProtegee><Accueil /></RouteProtegee>} />
    <Route path="/eglises" element={<RouteProtegee><ListeEglises /></RouteProtegee>} />
    <Route path="/eglises/:id" element={<RouteProtegee><DetailEglise /></RouteProtegee>} />
    <Route path="/recherche" element={<RouteProtegee><RechercheMembre /></RouteProtegee>} />
    <Route path="/bureau-national" element={<RouteProtegee><BureauNational /></RouteProtegee>} />
    <Route path="/bureaux" element={<RouteProtegee><Bureaux /></RouteProtegee>} />
    <Route path="/courriers" element={<RouteProtegee><Courriers /></RouteProtegee>} />
    <Route path="/documents" element={<RouteProtegee><Documents /></RouteProtegee>} />
    <Route path="/notifications" element={<RouteProtegee><Notifications /></RouteProtegee>} />
    <Route path="/finances" element={<RouteProtegee><Finances /></RouteProtegee>} />
    <Route path="/annexes" element={<RouteProtegee><Annexes /></RouteProtegee>} />
    <Route path="/geographie" element={<RouteProtegee><Geographie /></RouteProtegee>} />
    <Route path="/profil" element={<RouteProtegee><Profil /></RouteProtegee>} />
    <Route path="/administrateurs" element={<RouteProtegee><GestionAdministrateurs /></RouteProtegee>} />
    <Route path="/rapports" element={<RouteProtegee><Rapports /></RouteProtegee>} />
    <Route path="/membres" element={<RouteProtegee><Membres /></RouteProtegee>} />
    <Route path="/ia" element={<RouteProtegee><AssistantIA /></RouteProtegee>} />
    <Route path="/reunions" element={<RouteProtegee><Reunions /></RouteProtegee>} />
    <Route path="/parametres" element={<RouteProtegee roles={["COORDINATEUR"]}><Parametres /></RouteProtegee>} />
    <Route path="/national" element={<RouteProtegee><TableauDeBordNational /></RouteProtegee>} />
  </Routes>;
}
