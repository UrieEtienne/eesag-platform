import { useEffect, useState } from "react";
import client from "../../frontend/src/api/client";

export default function Systeme() {
  const [fonctionnalites, setFonctionnalites] = useState([]);
  const [options, setOptions] = useState([]);
  const [chargement, setChargement] = useState(true);
  const [erreur, setErreur] = useState("");
  const [message, setMessage] = useState("");

  const charger = async () => {
    setChargement(true);
    setErreur("");

    try {
      const [fonctionnalitesResponse, optionsResponse] =
        await Promise.all([
          client.get("/systeme/fonctionnalites/"),
          client.get("/systeme/options/"),
        ]);

      setFonctionnalites(
        fonctionnalitesResponse.data?.results ||
          fonctionnalitesResponse.data ||
          []
      );

      setOptions(
        optionsResponse.data?.results ||
          optionsResponse.data ||
          []
      );
    } catch (err) {
      setErreur(
        err.response?.data?.detail ||
          "Impossible de charger les paramètres du système."
      );
    } finally {
      setChargement(false);
    }
  };

  useEffect(() => {
    charger();
  }, []);

  const basculerFonctionnalite = async (fonctionnalite) => {
    setMessage("");
    setErreur("");

    try {
      const response = await client.post(
        `/systeme/fonctionnalites/${fonctionnalite.code}/toggle/`,
        {
          actif: !fonctionnalite.actif,
        }
      );

      const nouvelEtat = response.data?.actif;

      setFonctionnalites((precedentes) =>
        precedentes.map((item) =>
          item.code === fonctionnalite.code
            ? {
                ...item,
                actif: nouvelEtat,
              }
            : item
        )
      );

      setMessage(
        `${fonctionnalite.nom} : ${
          nouvelEtat ? "activée" : "désactivée"
        } dans le périmètre ${
          response.data?.scope || "actuel"
        }.`
      );
    } catch (err) {
      setErreur(
        err.response?.data?.detail ||
          "Impossible de modifier cette fonctionnalité."
      );
    }
  };

  return (
    <div>
      <div className="page-hero">
        <div>
          <span className="eyebrow">ADMINISTRATION</span>
          <h1>Système</h1>
          <p>
            Contrôle des fonctionnalités et des options de la
            plateforme EESAG.
          </p>
        </div>
      </div>

      {message && (
        <div className="console-success">
          {message}
        </div>
      )}

      {erreur && (
        <div className="console-error">
          {erreur}
        </div>
      )}

      {chargement ? (
        <section className="carte">
          <p>Chargement des paramètres du système...</p>
        </section>
      ) : (
        <>
          <section className="carte">
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                gap: 16,
                marginBottom: 20,
              }}
            >
              <div>
                <h2>Fonctionnalités</h2>
                <p className="sous-titre">
                  Activez ou désactivez les fonctionnalités
                  disponibles dans la plateforme.
                </p>
              </div>

              <button
                type="button"
                className="btn btn-secondaire"
                onClick={charger}
              >
                Actualiser
              </button>
            </div>

            {!fonctionnalites.length ? (
              <div className="empty-state">
                Aucune fonctionnalité disponible.
              </div>
            ) : (
              <div className="dashboard-grid">
                {fonctionnalites.map((fonctionnalite) => (
                  <article
                    className={`carte feature-card ${
                      fonctionnalite.actif
                        ? "enabled"
                        : "disabled"
                    }`}
                    key={fonctionnalite.code}
                  >
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        gap: 16,
                        alignItems: "flex-start",
                      }}
                    >
                      <div>
                        <h3>{fonctionnalite.nom}</h3>

                        {fonctionnalite.description && (
                          <p>
                            {fonctionnalite.description}
                          </p>
                        )}
                      </div>

                      <span
                        className={`status-chip ${
                          fonctionnalite.actif
                            ? "ok"
                            : "pending"
                        }`}
                      >
                        {fonctionnalite.actif
                          ? "Active"
                          : "Inactive"}
                      </span>
                    </div>

                    <button
                      type="button"
                      className="btn"
                      onClick={() =>
                        basculerFonctionnalite(
                          fonctionnalite
                        )
                      }
                    >
                      {fonctionnalite.actif
                        ? "Désactiver"
                        : "Activer"}
                    </button>
                  </article>
                ))}
              </div>
            )}
          </section>

          <section className="carte">
            <h2>Options disponibles</h2>

            <p className="sous-titre">
              Options et services configurés pour EESAG.
            </p>

            {!options.length ? (
              <div className="empty-state">
                Aucune option disponible.
              </div>
            ) : (
              <div className="dashboard-grid">
                {options.map((option) => (
                  <article
                    className="carte"
                    key={option.code || option.id}
                  >
                    <h3>
                      {option.nom ||
                        option.label ||
                        option.code}
                    </h3>

                    {option.description && (
                      <p>{option.description}</p>
                    )}

                    {option.prix !== undefined && (
                      <p>
                        <strong>
                          {option.gratuite
                            ? "Gratuite"
                            : `${Number(
                                option.prix || 0
                              ).toLocaleString(
                                "fr-FR"
                              )} ${
                                option.devise || "GNF"
                              }`}
                        </strong>
                      </p>
                    )}

                    {option.gratuite !== undefined && (
                      <span
                        className={`status-chip ${
                          option.gratuite
                            ? "ok"
                            : "pending"
                        }`}
                      >
                        {option.gratuite
                          ? "Gratuite"
                          : "Payante"}
                      </span>
                    )}
                  </article>
                ))}
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
}
