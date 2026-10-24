import { Routes, Route } from "react-router-dom";

import RouteProtegee from "./components/RouteProtegee";

import Connexion from "./pages/Connexion";
import Inscription from "./pages/Inscription";
import Profil from "./pages/Profil";

import GestionAdministrateurs from "./pages/GestionAdministrateurs";
import AdministrationEglise from "./pages/AdministrationEglise";
import AdministrationEglises from "./pages/AdministrationEglises";

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
  return (
    <Routes>

      {/* =====================================================
          PUBLIC
      ===================================================== */}

      <Route path="/connexion" element={<Connexion />} />
      <Route path="/inscription" element={<Inscription />} />


      {/* =====================================================
          ACCUEIL
      ===================================================== */}

      <Route
        path="/"
        element={
          <RouteProtegee>
            <Accueil />
          </RouteProtegee>
        }
      />


      {/* =====================================================
          COORDINATEUR DU SYSTEME
      ===================================================== */}

      <Route
        path="/admin"
        element={
          <RouteProtegee roles={["COORDINATEUR"]}>
            <AdministrationSysteme />
          </RouteProtegee>
        }
      />

      <Route
        path="/admin"
        element={
          <RouteProtegee roles={["COORDINATEUR"]}>
            <GestionAdministrateurs />
          </RouteProtegee>
        }
      />

      <Route
        path="/annonces-systeme"
        element={
          <RouteProtegee roles={["COORDINATEUR"]}>
            <Notifications />
          </RouteProtegee>
        }
      />

      <Route
        path="/parametres"
        element={
          <RouteProtegee roles={["COORDINATEUR"]}>
            <Parametres />
          </RouteProtegee>
        }
      />

      <Route
        path="/systeme"
        element={
          <RouteProtegee roles={["COORDINATEUR"]}>
            <Parametres />
          </RouteProtegee>
        }
      />


      {/* =====================================================
          BUREAU NATIONAL
      ===================================================== */}

      <Route
        path="/admin-eglises"
        element={
          <RouteProtegee
            roles={[
              "COORDINATEUR",
              "SUPERADMIN_INTL",
              "SUPERADMIN_NATIONAL",
            ]}
          >
            <AdministrationEglises />
          </RouteProtegee>
        }
      />

      <Route
        path="/national"
        element={
          <RouteProtegee
            roles={[
              "COORDINATEUR",
              "SUPERADMIN_INTL",
              "SUPERADMIN_NATIONAL",
            ]}
          >
            <TableauDeBordNational />
          </RouteProtegee>
        }
      />

      <Route
        path="/eglises"
        element={
          <RouteProtegee
            roles={[
              "COORDINATEUR",
              "SUPERADMIN_INTL",
              "SUPERADMIN_NATIONAL",
            ]}
          >
            <ListeEglises />
          </RouteProtegee>
        }
      />

      <Route
        path="/eglises/:id"
        element={
          <RouteProtegee
            roles={[
              "COORDINATEUR",
              "SUPERADMIN_INTL",
              "SUPERADMIN_NATIONAL",
            ]}
          >
            <DetailEglise />
          </RouteProtegee>
        }
      />

      <Route
        path="/bureaux"
        element={
          <RouteProtegee
            roles={[
              "COORDINATEUR",
              "SUPERADMIN_INTL",
              "SUPERADMIN_NATIONAL",
            ]}
          >
            <Bureaux />
          </RouteProtegee>
        }
      />


      {/* =====================================================
          EGLISE LOCALE
      ===================================================== */}

      <Route
        path="/eglise-dashboard"
        element={
          <RouteProtegee
            roles={[
              "ADMIN_LOCAL",
              "PASTEUR",
            ]}
          >
            <Accueil />
          </RouteProtegee>
        }
      />

      {/* ADMINISTRATION DE L'EGLISE
          ADMIN_LOCAL UNIQUEMENT */}
      <Route
        path="/eglise-administration"
        element={
          <RouteProtegee roles={["ADMIN_LOCAL"]}>
            <AdministrationEglise />
          </RouteProtegee>
        }
      />

      {/* GESTION DES UTILISATEURS DE L'EGLISE
          ADMIN_LOCAL UNIQUEMENT */}
      <Route
        path="/administrateurs"
        element={
          <RouteProtegee roles={["ADMIN_LOCAL"]}>
            <GestionAdministrateurs />
          </RouteProtegee>
        }
      />


      {/* =====================================================
          MEMBRES
      ===================================================== */}

      <Route
        path="/membres"
        element={
          <RouteProtegee
            roles={[
              "COORDINATEUR",
              "ADMIN_LOCAL",
              "PASTEUR",
            ]}
          >
            <Membres />
          </RouteProtegee>
        }
      />

      <Route
        path="/recherche"
        element={
          <RouteProtegee
            roles={[
              "COORDINATEUR",
              "ADMIN_LOCAL",
              "PASTEUR",
            ]}
          >
            <RechercheMembre />
          </RouteProtegee>
        }
      />


      {/* =====================================================
          COURRIERS
      ===================================================== */}

      {/* Envoi : ADMIN_LOCAL + PASTEUR */}
      <Route
        path="/courriers/envoyer"
        element={
          <RouteProtegee
            roles={[
              "ADMIN_LOCAL",
              "PASTEUR",
            ]}
          >
            <Courriers mode="envoyer" />
          </RouteProtegee>
        }
      />

      {/* Réception : ADMIN_LOCAL + PASTEUR */}
      <Route
        path="/courriers/recus"
        element={
          <RouteProtegee
            roles={[
              "ADMIN_LOCAL",
              "PASTEUR",
            ]}
          >
            <Courriers mode="recus" />
          </RouteProtegee>
        }
      />

      {/* Compatibilité ancienne URL */}
      <Route
        path="/courriers"
        element={
          <RouteProtegee
            roles={[
              "ADMIN_LOCAL",
              "PASTEUR",
            ]}
          >
            <Courriers mode="recus" />
          </RouteProtegee>
        }
      />


      {/* =====================================================
          DOCUMENTS
      ===================================================== */}

      <Route
        path="/documents"
        element={
          <RouteProtegee>
            <Documents />
          </RouteProtegee>
        }
      />


      {/* =====================================================
          NOTIFICATIONS
      ===================================================== */}

      <Route
        path="/notifications"
        element={
          <RouteProtegee>
            <Notifications />
          </RouteProtegee>
        }
      />


      {/* =====================================================
          FINANCES
      ===================================================== */}

      <Route
        path="/finances"
        element={
          <RouteProtegee
            roles={[
              "COORDINATEUR",
              "SUPERADMIN_INTL",
              "SUPERADMIN_NATIONAL",
              "ADMIN_LOCAL",
              "PASTEUR",
            ]}
          >
            <Finances />
          </RouteProtegee>
        }
      />


      {/* =====================================================
          ANNEXES
      ===================================================== */}

      <Route
        path="/annexes"
        element={
          <RouteProtegee
            roles={[
              "COORDINATEUR",
              "SUPERADMIN_INTL",
              "SUPERADMIN_NATIONAL",
              "ADMIN_LOCAL",
              "PASTEUR",
            ]}
          >
            <Annexes />
          </RouteProtegee>
        }
      />


      {/* =====================================================
          GEOGRAPHIE
      ===================================================== */}

      <Route
        path="/geographie"
        element={
          <RouteProtegee
            roles={[
              "COORDINATEUR",
              "SUPERADMIN_INTL",
              "SUPERADMIN_NATIONAL",
            ]}
          >
            <Geographie />
          </RouteProtegee>
        }
      />


      {/* =====================================================
          RAPPORTS
      ===================================================== */}

      <Route
        path="/rapports"
        element={
          <RouteProtegee>
            <Rapports />
          </RouteProtegee>
        }
      />


      {/* =====================================================
          IA
      ===================================================== */}

      <Route
        path="/ia"
        element={
          <RouteProtegee>
            <AssistantIA />
          </RouteProtegee>
        }
      />


      {/* =====================================================
          REUNIONS
      ===================================================== */}

      <Route
        path="/reunions"
        element={
          <RouteProtegee>
            <Reunions />
          </RouteProtegee>
        }
      />


      {/* =====================================================
          BUREAU NATIONAL
      ===================================================== */}

      <Route
        path="/bureau-national"
        element={
          <RouteProtegee>
            <BureauNational />
          </RouteProtegee>
        }
      />


      {/* =====================================================
          PROFIL
      ===================================================== */}

      <Route
        path="/profil"
        element={
          <RouteProtegee>
            <Profil />
          </RouteProtegee>
        }
      />

    </Routes>
  );
}