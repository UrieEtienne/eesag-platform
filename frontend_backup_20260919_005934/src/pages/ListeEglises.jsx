import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import client from "../api/client";
import { useAuth } from "../context/AuthContext";

export default function ListeEglises() {
  const [eglises, setEglises] = useState([]);
  const [recherche, setRecherche] = useState("");
  const [statutFiltre, setStatutFiltre] = useState("");
  const [erreur, setErreur] = useState("");
  const [chargement, setChargement] = useState(true);

  const {
    estCoordinateur,
    estBureauNationalGeneral,
    estBureauNational,
    utilisateur,
  } = useAuth();

  const peutAdministrer =
    estCoordinateur || estBureauNationalGeneral;

  const lectureSeule =
    estBureauNational && !estBureauNationalGeneral;

  /* =========================================================
     CHARGEMENT DES ÉGLISES
  ========================================================== */

  const charger = async () => {
    setChargement(true);
    setErreur("");

    try {
      const params = {};

      if (recherche.trim()) {
        params.search = recherche.trim();
      }

      if (statutFiltre) {
        params.statut = statutFiltre;
      }

      const response = await client.get("/eglises/", {
        params,
      });

      const data = response.data;

      if (Array.isArray(data)) {
        setEglises(data);
      } else if (Array.isArray(data?.results)) {
        setEglises(data.results);
      } else {
        setEglises([]);
      }
    } catch (error) {
      console.error(
        "Erreur chargement des églises :",
        error
      );

      setErreur(
        error.response?.data?.detail ||
          "Impossible de charger l'annuaire des églises."
      );

      setEglises([]);
    } finally {
      setChargement(false);
    }
  };

  /* =========================================================
     RECHERCHE
  ========================================================== */

  useEffect(() => {
    const timer = setTimeout(() => {
      charger();
    }, 250);

    return () => clearTimeout(timer);

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [recherche, statutFiltre]);

  /* =========================================================
     AFFICHAGE
  ========================================================== */

  return (
    <div className="page">

      {/* =====================================================
          EN-TÊTE
      ====================================================== */}

      <div className="page-hero">
        <div>
          <span className="eyebrow">
            ANNUAIRE NATIONAL
          </span>

          <h1>Églises</h1>

          <p>
            Consultez les églises enregistrées dans
            le réseau EESAG selon votre niveau d'accès.
          </p>
        </div>
      </div>

      {/* =====================================================
          BUREAU NATIONAL SPÉCIALISÉ
      ====================================================== */}

      {lectureSeule && (
        <div className="console-note">
          Votre bureau national spécialisé dispose
          uniquement de l'accès à l'annuaire. Il ne peut
          pas créer une église ni administrer les comptes
          des églises.
        </div>
      )}

      {/* =====================================================
          ERREUR
      ====================================================== */}

      {erreur && (
        <div className="console-error">
          {erreur}
        </div>
      )}

      {/* =====================================================
          FILTRES
      ====================================================== */}

      <div className="filtres">

        <input
          type="search"
          placeholder="Rechercher une église..."
          value={recherche}
          onChange={(e) => {
            setRecherche(e.target.value);
          }}
        />

        <select
          value={statutFiltre}
          onChange={(e) => {
            setStatutFiltre(e.target.value);
          }}
        >
          <option value="">
            Tous les statuts
          </option>

          <option value="ACTIVE">
            Active
          </option>

          <option value="SUSPENDUE">
            Suspendue
          </option>

          <option value="FERMEE">
            Fermée
          </option>
        </select>

      </div>

      {/* =====================================================
          TABLEAU
      ====================================================== */}

      <div className="carte table-wrap">

        {chargement ? (
          <div className="empty-state">
            Chargement des églises...
          </div>
        ) : (
          <table>

            <thead>
              <tr>
                <th>Code</th>
                <th>Église</th>
                <th>Région</th>
                <th>Préfecture</th>
                <th>Statut</th>

                {peutAdministrer && (
                  <th>Membres</th>
                )}

                <th>Action</th>
              </tr>
            </thead>

            <tbody>

              {eglises.map((eglise) => {

                const estMonEglise =
                  utilisateur?.eglise != null &&
                  String(utilisateur.eglise) ===
                    String(eglise.id);

                const peutOuvrir =
                  peutAdministrer ||
                  estMonEglise;

                return (
                  <tr key={eglise.id}>

                    <td>
                      <b>
                        {eglise.code || "—"}
                      </b>
                    </td>

                    <td>
                      <b>
                        {eglise.nom || "—"}
                      </b>

                      {eglise.adresse_precise && (
                        <div className="texte-secondaire">
                          {eglise.adresse_precise}
                        </div>
                      )}

                      {eglise.telephone && (
                        <div className="texte-secondaire">
                          {eglise.telephone}
                        </div>
                      )}
                    </td>

                    <td>
                      {eglise.region_nom ||
                        eglise.region?.nom ||
                        "—"}
                    </td>

                    <td>
                      {eglise.prefecture_nom ||
                        eglise.prefecture?.nom ||
                        "—"}
                    </td>

                    <td>
                      {eglise.statut === "ACTIVE" ? (
                        <span className="status-active">
                          Active
                        </span>
                      ) : eglise.statut === "SUSPENDUE" ? (
                        <span className="status-off">
                          Suspendue
                        </span>
                      ) : eglise.statut === "FERMEE" ? (
                        <span className="status-off">
                          Fermée
                        </span>
                      ) : (
                        <span className="tag">
                          {eglise.statut || "—"}
                        </span>
                      )}
                    </td>

                    {peutAdministrer && (
                      <td>
                        {eglise.nombre_membres ??
                          eglise.nb_membres ??
                          "—"}
                      </td>
                    )}

                    <td>
                      {peutOuvrir ? (
                        <Link
                          className="btn btn-petit btn-secondaire"
                          to={`/eglises/${eglise.id}`}
                        >
                          Ouvrir
                        </Link>
                      ) : (
                        <span className="tag">
                          Annuaire
                        </span>
                      )}
                    </td>

                  </tr>
                );
              })}

              {eglises.length === 0 && (
                <tr>
                  <td
                    colSpan={
                      peutAdministrer ? 7 : 6
                    }
                  >
                    <div className="empty-state">

                      <div
                        style={{
                          fontSize: "40px",
                          marginBottom: "10px",
                        }}
                      >
                        🏛
                      </div>

                      <h3>
                        Aucune église trouvée
                      </h3>

                      <p>
                        Aucune église ne correspond
                        aux critères de recherche.
                      </p>

                    </div>
                  </td>
                </tr>
              )}

            </tbody>

          </table>
        )}

      </div>

    </div>
  );
}