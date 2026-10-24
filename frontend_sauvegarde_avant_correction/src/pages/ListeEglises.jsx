import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import client from "../api/client";
import { useAuth } from "../context/AuthContext";

export default function ListeEglises() {
  const [eglises, setEglises] = useState([]);
  const [recherche, setRecherche] = useState("");
  const [erreur, setErreur] = useState("");
  const [chargement, setChargement] = useState(true);

  const {
    estCoordinateur,
    estBureauNationalGeneral,
    estBureauNational,
    utilisateur,
  } = useAuth();

  const peutAdministrer =
    Boolean(estCoordinateur) || Boolean(estBureauNationalGeneral);

  const lectureSeule =
    Boolean(estBureauNational) && !Boolean(estBureauNationalGeneral);

  const charger = useCallback(async () => {
    setErreur("");
    setChargement(true);

    try {
      const params = {};

      if (recherche.trim()) {
        params.search = recherche.trim();
      }

      const reponse = await client.get("/eglises/", { params });
      const donnees = reponse.data;

      setEglises(
        Array.isArray(donnees)
          ? donnees
          : Array.isArray(donnees?.results)
            ? donnees.results
            : []
      );
    } catch (error) {
      setErreur(
        error.response?.data?.detail ||
          "Impossible de charger l’annuaire des églises."
      );
      setEglises([]);
    } finally {
      setChargement(false);
    }
  }, [recherche]);

  useEffect(() => {
    const temporisation = setTimeout(() => {
      charger();
    }, 250);

    return () => clearTimeout(temporisation);
  }, [charger]);

  return (
    <div>
      <div className="page-hero">
        <div>
          <span className="eyebrow">ANNUAIRE EESAG</span>
          <h1>Liste des églises</h1>
          <p>
            Consultez les églises enregistrées et leur statut. La création et
            l’activation se font dans l’espace d’administration autorisé.
          </p>
        </div>
      </div>

      {lectureSeule && (
        <div className="console-note">
          Votre bureau national spécialisé dispose d’un accès en lecture seule
          à cet annuaire. Il ne peut pas créer d’église, activer une plateforme
          ou administrer les comptes des églises depuis cette page.
        </div>
      )}

      {erreur && <div className="console-error">{erreur}</div>}

      <div className="filtres">
        <input
          type="search"
          placeholder="Rechercher par nom ou code d’église…"
          value={recherche}
          onChange={(event) => setRecherche(event.target.value)}
          aria-label="Rechercher une église"
        />
      </div>

      <div className="carte table-wrap">
        <table>
          <thead>
            <tr>
              <th>Code</th>
              <th>Église</th>
              <th>Région</th>
              <th>Statut plateforme</th>
              {peutAdministrer && <th>Membres actifs</th>}
              <th>Action</th>
            </tr>
          </thead>

          <tbody>
            {chargement ? (
              <tr>
                <td colSpan={peutAdministrer ? 6 : 5}>
                  Chargement des églises…
                </td>
              </tr>
            ) : eglises.length === 0 ? (
              <tr>
                <td colSpan={peutAdministrer ? 6 : 5}>
                  <div className="empty-state">
                    {erreur
                      ? "Les données n’ont pas pu être chargées."
                      : "Aucune église trouvée."}
                  </div>
                </td>
              </tr>
            ) : (
              eglises.map((eglise) => {
                const memeEglise =
                  utilisateur?.eglise === eglise.id ||
                  utilisateur?.eglise_id === eglise.id;

                const peutOuvrir = peutAdministrer || memeEglise;

                return (
                  <tr key={eglise.id}>
                    <td>
                      <b>{eglise.code || "—"}</b>
                    </td>

                    <td>{eglise.nom || "Sans nom"}</td>

                    <td>{eglise.region_nom || "—"}</td>

                    <td>
                      {eglise.plateforme_active ? (
                        <span className="status-active">Active</span>
                      ) : (
                        <span className="status-off">À activer</span>
                      )}
                    </td>

                    {peutAdministrer && (
                      <td>{eglise.nombre_membres ?? "—"}</td>
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
                        <span className="tag">Annuaire</span>
                      )}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}