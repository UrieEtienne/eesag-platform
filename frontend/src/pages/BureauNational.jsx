import { useCallback, useEffect, useMemo, useState } from "react";
import client, { mediaUrl } from "../api/client";
import { useAuth } from "../context/AuthContext";
import "./BureauNational.css";

const ANNEE_ACTUELLE = new Date().getFullYear();

const ANNEES = [
  ANNEE_ACTUELLE - 1,
  ANNEE_ACTUELLE,
  ANNEE_ACTUELLE + 1,
];

function extraireListe(data) {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.results)) return data.results;
  return [];
}

function nomMembre(membre) {
  return (
    membre?.nom_complet ||
    [membre?.prenom, membre?.nom].filter(Boolean).join(" ") ||
    membre?.identifiant ||
    "Membre"
  );
}

function initiale(membre) {
  return nomMembre(membre).charAt(0).toUpperCase();
}

function normaliserPhoto(photo) {
  if (!photo) return null;

  try {
    return mediaUrl(photo);
  } catch {
    return photo;
  }
}

export default function BureauNational() {
  const { estNational } = useAuth();

  const [bureaux, setBureaux] = useState([]);
  const [mandats, setMandats] = useState([]);
  const [membresIndependants, setMembresIndependants] = useState([]);

  const [annee, setAnnee] = useState(ANNEE_ACTUELLE);
  const [bureauSelectionne, setBureauSelectionne] = useState("");

  const [chargement, setChargement] = useState(true);
  const [erreur, setErreur] = useState("");

  const chargerBureaux = useCallback(async () => {
    setChargement(true);
    setErreur("");

    try {
      const [
        bureauxResponse,
        mandatsResponse,
        independantsResponse,
      ] = await Promise.all([
        client.get("/bureaux/", {
          params: {
            niveau: "NATIONAL",
            actif: true,
          },
        }),

        client.get("/bureau-membres/", {
          params: {
            annee,
            actif: true,
          },
        }),

        client.get("/bureau-membres-independants/", {
          params: {
            annee,
            actif: true,
          },
        }),
      ]);

      const tousLesBureaux = extraireListe(
        bureauxResponse.data
      ).filter(
        (bureau) =>
          bureau.niveau === "NATIONAL" &&
          bureau.actif === true
      );

      const tousLesMandats = extraireListe(
        mandatsResponse.data
      ).filter(
        (mandat) =>
          Number(mandat.annee) === Number(annee) &&
          mandat.actif === true
      );

      const tousLesIndependants = extraireListe(
        independantsResponse.data
      ).filter(
        (membre) =>
          Number(membre.annee) === Number(annee) &&
          membre.actif === true
      );

      setBureaux(tousLesBureaux);
      setMandats(tousLesMandats);
      setMembresIndependants(tousLesIndependants);

      /*
       * Sélection automatique du premier bureau.
       * Si un bureau était déjà sélectionné et existe toujours,
       * on le conserve.
       */
      setBureauSelectionne((ancienneSelection) => {
        const existe = tousLesBureaux.some(
          (bureau) =>
            String(bureau.id) === String(ancienneSelection)
        );

        if (existe) {
          return ancienneSelection;
        }

        return tousLesBureaux.length > 0
          ? String(tousLesBureaux[0].id)
          : "";
      });
    } catch (error) {
      console.error(
        "Erreur de chargement des bureaux nationaux :",
        error
      );

      setErreur(
        error?.response?.data?.detail ||
          "Impossible de charger les bureaux nationaux et leurs membres."
      );
    } finally {
      setChargement(false);
    }
  }, [annee]);

  useEffect(() => {
    chargerBureaux();
  }, [chargerBureaux]);

  const bureauActuel = useMemo(() => {
    return bureaux.find(
      (bureau) =>
        String(bureau.id) === String(bureauSelectionne)
    );
  }, [bureaux, bureauSelectionne]);

  /*
   * Fusion des deux sources :
   *
   * 1. BureauMembreMandat
   *    -> personne possédant un compte EESAG
   *
   * 2. BureauMembre
   *    -> personne indépendante sans compte EESAG
   */
  const membresDuBureau = useMemo(() => {
    if (!bureauSelectionne) {
      return [];
    }

    const mandatsDuBureau = mandats
      .filter(
        (mandat) =>
          String(mandat.bureau) ===
          String(bureauSelectionne)
      )
      .map((mandat) => ({
        id: `compte-${mandat.id}`,
        nom: nomMembre(mandat),
        poste: mandat.poste || "Membre",
        photo: normaliserPhoto(mandat.photo),
        source: "compte",
        identifiant: mandat.identifiant,
      }));

    const independantsDuBureau = membresIndependants
      .filter(
        (membre) =>
          String(membre.bureau) ===
          String(bureauSelectionne)
      )
      .map((membre) => ({
        id: `independant-${membre.id}`,
        nom: membre.nom_complet || "Membre",
        poste: membre.poste || "Membre",
        photo: normaliserPhoto(membre.photo),
        source: "independant",
      }));

    return [
      ...mandatsDuBureau,
      ...independantsDuBureau,
    ];
  }, [
    bureauSelectionne,
    mandats,
    membresIndependants,
  ]);

  return (
    <div className="bureau-national-page">

      {/* =====================================================
          EN-TÊTE
      ====================================================== */}
      <section className="bureau-national-hero">
        <div className="bureau-national-hero-content">
          <span className="bureau-national-eyebrow">
            GOUVERNANCE EESAG
          </span>

          <h1>Bureaux nationaux</h1>

          <p>
            Sélectionnez un bureau pour consulter sa composition
            pour l'année choisie.
          </p>
        </div>

        <div className="bureau-national-year">
          <label htmlFor="bureau-national-year">
            Année
          </label>

          <select
            id="bureau-national-year"
            value={annee}
            onChange={(event) =>
              setAnnee(Number(event.target.value))
            }
          >
            {ANNEES.map((valeur) => (
              <option key={valeur} value={valeur}>
                {valeur}
              </option>
            ))}
          </select>
        </div>
      </section>

      {/* =====================================================
          SÉLECTION DU BUREAU + COMPTEUR
      ====================================================== */}
      <section className="bureau-national-selection">
        <div className="bureau-national-select-wrapper">
          <label htmlFor="bureau-national-select-page">
            Sélectionner un bureau national
          </label>

          <select
            id="bureau-national-select-page"
            value={bureauSelectionne}
            onChange={(event) =>
              setBureauSelectionne(event.target.value)
            }
            disabled={
              chargement || bureaux.length === 0
            }
          >
            {bureaux.length === 0 ? (
              <option value="">
                Aucun bureau disponible
              </option>
            ) : (
              bureaux.map((bureau) => (
                <option
                  key={bureau.id}
                  value={bureau.id}
                >
                  {bureau.nom}
                </option>
              ))
            )}
          </select>
        </div>

        <div className="bureau-national-count">
          <div className="bureau-national-count-icon">
            <svg
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"
              />
              <circle
                cx="9"
                cy="7"
                r="4"
              />
              <path
                d="M22 21v-2a4 4 0 0 0-3-3.87"
              />
              <path
                d="M16 3.13a4 4 0 0 1 0 7.75"
              />
            </svg>
          </div>

          <div>
            <span>Membres affichés</span>
            <strong>
              {membresDuBureau.length}
            </strong>
          </div>
        </div>
      </section>

      {/* =====================================================
          ALERTES
      ====================================================== */}
      {erreur && (
        <div
          className="bureau-national-alert"
          role="alert"
        >
          {erreur}
        </div>
      )}

      {/* =====================================================
          CHARGEMENT
      ====================================================== */}
      {chargement ? (
        <div className="bureau-national-empty">
          Chargement de la composition…
        </div>
      ) : !bureauActuel ? (
        <div className="bureau-national-empty">
          Aucun bureau national disponible.
        </div>
      ) : membresDuBureau.length === 0 ? (
        <div className="bureau-national-empty">
          Aucun membre enregistré pour ce bureau en{" "}
          {annee}.
        </div>
      ) : (
        /* ===================================================
           MEMBRES HORIZONTAUX
        ==================================================== */
        <section className="bureau-national-members">
          <div className="bureau-national-members-grid">
            {membresDuBureau.map((membre) => (
              <article
                key={membre.id}
                className="bureau-national-member-card"
              >
                <div className="bureau-national-member-photo">
                  {membre.photo ? (
                    <img
                      src={membre.photo}
                      alt={membre.nom}
                    />
                  ) : (
                    <div className="bureau-national-member-placeholder">
                      {initiale(membre)}
                    </div>
                  )}
                </div>

                <div className="bureau-national-member-info">
                  <h2>{membre.nom}</h2>

                  <p>{membre.poste}</p>
                </div>
              </article>
            ))}
          </div>
        </section>
      )}

      {/* =====================================================
          ZONE ADMINISTRATION
          Conservée uniquement pour les utilisateurs habilités.
      ====================================================== */}
      {estNational && false && (
        <div />
      )}
    </div>
  );
}
