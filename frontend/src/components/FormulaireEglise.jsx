import { useEffect, useState } from "react";
import client from "../api/client";

const initial = {
  nom: "",
  region: "",
  prefecture: "",
  district: "",
  commune: "",
  adresse_precise: "",
  telephone: "",
  email: "",
  date_creation: "",

  responsable_nom: "",
  responsable_telephone: "",
  responsable_email: "",

  creer_compte_admin: true,
  admin_nom: "",
  admin_prenom: "",
  admin_telephone: "",
  admin_email: "",
  admin_mot_de_passe: "",
  admin_confirmation: "",
};

const normaliserNumero = (value) => {
  return String(value || "").trim();
};

const extraireListe = (data) => {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.results)) return data.results;
  return [];
};

export default function FormulaireEglise({ onCree }) {
  const [form, setForm] = useState(initial);

  const [regions, setRegions] = useState([]);
  const [prefectures, setPrefectures] = useState([]);
  const [districts, setDistricts] = useState([]);
  const [communes, setCommunes] = useState([]);

  const [chargementGeo, setChargementGeo] = useState(false);

  const [ajoutOuvert, setAjoutOuvert] = useState(null);
  const [nouveauNom, setNouveauNom] = useState("");
  const [ajoutChargement, setAjoutChargement] = useState(false);

  const [message, setMessage] = useState("");
  const [erreur, setErreur] = useState("");
  const [creation, setCreation] = useState(false);
  const [resultat, setResultat] = useState(null);

  const modifier = (champ, valeur) => {
    setForm((ancien) => ({
      ...ancien,
      [champ]: valeur,
    }));
  };

  /* =========================================================
     CHARGEMENT DES RÉGIONS
     ========================================================= */

  const chargerRegions = async () => {
    try {
      const response = await client.get("/geo/regions/");
      setRegions(extraireListe(response.data));
    } catch (error) {
      console.error("Erreur régions :", error);
      setRegions([]);
    }
  };

  useEffect(() => {
    chargerRegions();
  }, []);

  /* =========================================================
     CHARGEMENT DES PRÉFECTURES
     ========================================================= */

  useEffect(() => {
    if (!form.region) {
      setPrefectures([]);
      return;
    }

    const charger = async () => {
      setChargementGeo(true);

      try {
        const response = await client.get("/geo/prefectures/", {
          params: {
            region: form.region,
          },
        });

        setPrefectures(extraireListe(response.data));
      } catch (error) {
        console.error("Erreur préfectures :", error);
        setPrefectures([]);
      } finally {
        setChargementGeo(false);
      }
    };

    charger();
  }, [form.region]);

  /* =========================================================
     CHARGEMENT DES DISTRICTS
     ========================================================= */

  useEffect(() => {
    if (!form.prefecture) {
      setDistricts([]);
      return;
    }

    const charger = async () => {
      setChargementGeo(true);

      try {
        const response = await client.get("/geo/districts/", {
          params: {
            prefecture: form.prefecture,
          },
        });

        setDistricts(extraireListe(response.data));
      } catch (error) {
        console.error("Erreur districts :", error);
        setDistricts([]);
      } finally {
        setChargementGeo(false);
      }
    };

    charger();
  }, [form.prefecture]);

  /* =========================================================
     CHARGEMENT DES COMMUNES
     ========================================================= */

  useEffect(() => {
    if (!form.district) {
      setCommunes([]);
      return;
    }

    const charger = async () => {
      setChargementGeo(true);

      try {
        const response = await client.get("/geo/communes/", {
          params: {
            district: form.district,
          },
        });

        setCommunes(extraireListe(response.data));
      } catch (error) {
        console.error("Erreur communes :", error);
        setCommunes([]);
      } finally {
        setChargementGeo(false);
      }
    };

    charger();
  }, [form.district]);

  /* =========================================================
     AJOUT D'UNE DONNÉE GÉOGRAPHIQUE
     ========================================================= */

  const ouvrirAjout = (type) => {
    setAjoutOuvert(type);
    setNouveauNom("");
    setErreur("");
  };

  const fermerAjout = () => {
    setAjoutOuvert(null);
    setNouveauNom("");
  };

  const ajouterGeographie = async () => {
    const nom = nouveauNom.trim();

    if (!nom) {
      setErreur("Veuillez saisir un nom.");
      return;
    }

    setAjoutChargement(true);
    setErreur("");
    setMessage("");

    try {
      let endpoint = "";
      let payload = { nom };

      if (ajoutOuvert === "region") {
        endpoint = "/geo/regions/";
      }

      if (ajoutOuvert === "prefecture") {
        endpoint = "/geo/prefectures/";
        payload = {
          nom,
          region: form.region,
        };
      }

      if (ajoutOuvert === "district") {
        endpoint = "/geo/districts/";
        payload = {
          nom,
          prefecture: form.prefecture,
        };
      }

      if (ajoutOuvert === "commune") {
        endpoint = "/geo/communes/";
        payload = {
          nom,
          district: form.district,
        };
      }

      if (!endpoint) {
        throw new Error("Type géographique inconnu.");
      }

      const response = await client.post(endpoint, payload);
      const objet = response.data;

      if (ajoutOuvert === "region") {
        await chargerRegions();

        if (objet?.id) {
          modifier("region", objet.id);
        }
      }

      if (ajoutOuvert === "prefecture") {
        const r = await client.get("/geo/prefectures/", {
          params: {
            region: form.region,
          },
        });

        setPrefectures(extraireListe(r.data));

        if (objet?.id) {
          modifier("prefecture", objet.id);
        }
      }

      if (ajoutOuvert === "district") {
        const r = await client.get("/geo/districts/", {
          params: {
            prefecture: form.prefecture,
          },
        });

        setDistricts(extraireListe(r.data));

        if (objet?.id) {
          modifier("district", objet.id);
        }
      }

      if (ajoutOuvert === "commune") {
        const r = await client.get("/geo/communes/", {
          params: {
            district: form.district,
          },
        });

        setCommunes(extraireListe(r.data));

        if (objet?.id) {
          modifier("commune", objet.id);
        }
      }

      setMessage(
        `${nom} a été ajouté au référentiel géographique.`
      );

      fermerAjout();
    } catch (error) {
      console.error(error);

      const data = error.response?.data;

      if (typeof data === "string") {
        setErreur(data);
      } else if (data?.detail) {
        setErreur(data.detail);
      } else {
        setErreur(
          Object.entries(data || {})
            .map(([champ, valeur]) => {
              const texte = Array.isArray(valeur)
                ? valeur.join(", ")
                : String(valeur);

              return `${champ} : ${texte}`;
            })
            .join(" | ") ||
            "Impossible d'ajouter cette donnée géographique."
        );
      }
    } finally {
      setAjoutChargement(false);
    }
  };

  /* =========================================================
     CRÉATION DE L'ÉGLISE + ADMIN
     ========================================================= */

  const soumettre = async (event) => {
    event.preventDefault();

    setErreur("");
    setMessage("");
    setResultat(null);

    if (!form.nom.trim()) {
      setErreur("Le nom de l'église est obligatoire.");
      return;
    }

    if (!form.region) {
      setErreur("Veuillez sélectionner ou créer une région.");
      return;
    }

    if (!form.prefecture) {
      setErreur("Veuillez sélectionner ou créer une préfecture.");
      return;
    }

    if (!form.district) {
      setErreur("Veuillez sélectionner ou créer un district.");
      return;
    }

    if (form.creer_compte_admin) {
      if (!form.admin_nom.trim()) {
        setErreur("Le nom de l'administrateur est obligatoire.");
        return;
      }

      if (!form.admin_prenom.trim()) {
        setErreur("Le prénom de l'administrateur est obligatoire.");
        return;
      }

      if (!form.admin_telephone.trim()) {
        setErreur(
          "Le téléphone de l'administrateur est obligatoire."
        );
        return;
      }

      if (!form.admin_mot_de_passe) {
        setErreur(
          "Le mot de passe de l'administrateur est obligatoire."
        );
        return;
      }

      if (
        form.admin_mot_de_passe !==
        form.admin_confirmation
      ) {
        setErreur(
          "Les deux mots de passe administrateur ne correspondent pas."
        );
        return;
      }
    }

    setCreation(true);

    try {
      const payload = {
        nom: form.nom.trim(),

        region: form.region,
        prefecture: form.prefecture,
        district: form.district,
        commune: form.commune || null,

        adresse_precise: form.adresse_precise.trim(),
        telephone: normaliserNumero(form.telephone),
        email: form.email.trim(),
        date_creation: form.date_creation || null,

        responsable_nom: form.responsable_nom.trim(),
        responsable_telephone: normaliserNumero(
          form.responsable_telephone
        ),
        responsable_email:
          form.responsable_email.trim(),

        creer_compte_admin: form.creer_compte_admin,

        ...(form.creer_compte_admin
          ? {
              admin_nom: form.admin_nom.trim(),
              admin_prenom: form.admin_prenom.trim(),
              admin_telephone:
                normaliserNumero(
                  form.admin_telephone
                ),
              admin_email:
                form.admin_email.trim(),
              admin_mot_de_passe:
                form.admin_mot_de_passe,
              admin_confirmation:
                form.admin_confirmation,
            }
          : {}),
      };

      const response = await client.post(
        "/eglises/",
        payload
      );

      setResultat(response.data);

      setMessage(
        "Église créée avec succès. Le compte administrateur est lié à cette église."
      );

      onCree?.(response.data);
    } catch (error) {
      console.error(error);

      const data = error.response?.data;

      if (typeof data === "string") {
        setErreur(data);
      } else if (data?.detail) {
        setErreur(data.detail);
      } else {
        setErreur(
          Object.entries(data || {})
            .map(([champ, valeur]) => {
              const texte = Array.isArray(valeur)
                ? valeur.join(", ")
                : typeof valeur === "object"
                  ? JSON.stringify(valeur)
                  : String(valeur);

              return `${champ} : ${texte}`;
            })
            .join(" | ") ||
            "Impossible de créer l'église."
        );
      }
    } finally {
      setCreation(false);
    }
  };

  /* =========================================================
     AFFICHAGE D'UN CHAMP GÉOGRAPHIQUE
     ========================================================= */

  const champGeo = ({
    label,
    value,
    options,
    type,
    disabled = false,
    obligatoire = true,
    aide,
  }) => {
    return (
      <div className="form-champ">
        <label>
          {label}
          {obligatoire ? " *" : ""}
        </label>

        <div
          style={{
            display: "flex",
            gap: 8,
            alignItems: "stretch",
          }}
        >
          <select
            value={value || ""}
            disabled={disabled}
            onChange={(event) =>
              modifier(type, event.target.value)
            }
            style={{
              flex: 1,
              minWidth: 0,
            }}
          >
            <option value="">
              {disabled
                ? `Sélectionnez d'abord le niveau précédent`
                : options.length
                  ? `Sélectionner ${label.toLowerCase()}`
                  : `Aucune ${label.toLowerCase()} enregistrée`}
            </option>

            {options.map((item) => (
              <option
                key={item.id}
                value={item.id}
              >
                {item.nom}
              </option>
            ))}
          </select>

          <button
            type="button"
            className="btn btn-secondaire"
            onClick={() => ouvrirAjout(type)}
            disabled={
              type === "prefecture" && !form.region ||
              type === "district" && !form.prefecture ||
              type === "commune" && !form.district
            }
            style={{
              whiteSpace: "nowrap",
            }}
          >
            ＋ Ajouter
          </button>
        </div>

        {aide && (
          <small
            style={{
              display: "block",
              marginTop: 5,
              opacity: 0.7,
            }}
          >
            {aide}
          </small>
        )}
      </div>
    );
  };

  return (
    <div>
      <form onSubmit={soumettre}>
        {/* =====================================================
            ÉGLISE
        ====================================================== */}

        <section className="carte">
          <div className="page-section-heading">
            <div>
              <span className="eyebrow">
                NOUVELLE ÉGLISE
              </span>
              <h3>Informations de l'église</h3>
            </div>
          </div>

          <div className="form-grille">
            <div className="form-champ">
              <label htmlFor="eglise-nom">
                Nom de l'église *
              </label>

              <input
                id="eglise-nom"
                value={form.nom}
                onChange={(e) =>
                  modifier("nom", e.target.value)
                }
                placeholder="Ex. Église de Conakry"
                required
              />
            </div>

            <div className="form-champ">
              <label htmlFor="date-creation">
                Date de création
              </label>

              <input
                id="date-creation"
                type="date"
                value={form.date_creation}
                onChange={(e) =>
                  modifier(
                    "date_creation",
                    e.target.value
                  )
                }
              />
            </div>
          </div>
        </section>

        {/* =====================================================
            LOCALISATION
        ====================================================== */}

        <section
          className="carte"
          style={{ marginTop: 20 }}
        >
          <div className="page-section-heading">
            <div>
              <span className="eyebrow">
                LOCALISATION
              </span>
              <h3>Localisation de l'église</h3>

              <p>
                Si une localité n'existe pas encore,
                utilisez le bouton « ＋ Ajouter ».
              </p>
            </div>
          </div>

          <div className="form-grille">
            {champGeo({
              label: "Région",
              value: form.region,
              options: regions,
              type: "region",
              aide:
                "Le Bureau national peut ajouter une nouvelle région.",
            })}

            {champGeo({
              label: "Préfecture",
              value: form.prefecture,
              options: prefectures,
              type: "prefecture",
              disabled: !form.region,
              aide:
                "Choisissez d'abord la région.",
            })}

            {champGeo({
              label: "District",
              value: form.district,
              options: districts,
              type: "district",
              disabled: !form.prefecture,
              aide:
                "Choisissez d'abord la préfecture.",
            })}

            {champGeo({
              label: "Commune",
              value: form.commune,
              options: communes,
              type: "commune",
              disabled: !form.district,
              obligatoire: false,
              aide:
                "La commune est facultative.",
            })}
          </div>

          <div className="form-champ">
            <label htmlFor="adresse-precise">
              Adresse précise
            </label>

            <textarea
              id="adresse-precise"
              value={form.adresse_precise}
              onChange={(e) =>
                modifier(
                  "adresse_precise",
                  e.target.value
                )
              }
              placeholder="Quartier, secteur, rue, repère..."
              rows={3}
            />
          </div>
        </section>

        {/* =====================================================
            CONTACT
        ====================================================== */}

        <section
          className="carte"
          style={{ marginTop: 20 }}
        >
          <div className="page-section-heading">
            <div>
              <span className="eyebrow">
                CONTACT
              </span>
              <h3>Coordonnées de l'église</h3>
            </div>
          </div>

          <div className="form-grille">
            <div className="form-champ">
              <label htmlFor="eglise-telephone">
                Téléphone
              </label>

              <input
                id="eglise-telephone"
                value={form.telephone}
                onChange={(e) =>
                  modifier(
                    "telephone",
                    e.target.value
                  )
                }
                placeholder="+224..."
              />
            </div>

            <div className="form-champ">
              <label htmlFor="eglise-email">
                Email
              </label>

              <input
                id="eglise-email"
                type="email"
                value={form.email}
                onChange={(e) =>
                  modifier(
                    "email",
                    e.target.value
                  )
                }
                placeholder="eglise@example.com"
              />
            </div>
          </div>
        </section>

        {/* =====================================================
            RESPONSABLE
        ====================================================== */}

        <section
          className="carte"
          style={{ marginTop: 20 }}
        >
          <div className="page-section-heading">
            <div>
              <span className="eyebrow">
                RESPONSABLE
              </span>
              <h3>Responsable de l'église</h3>
            </div>
          </div>

          <div className="form-grille">
            <div className="form-champ">
              <label>Nom complet</label>

              <input
                value={form.responsable_nom}
                onChange={(e) =>
                  modifier(
                    "responsable_nom",
                    e.target.value
                  )
                }
                placeholder="Nom du responsable"
              />
            </div>

            <div className="form-champ">
              <label>Téléphone</label>

              <input
                value={form.responsable_telephone}
                onChange={(e) =>
                  modifier(
                    "responsable_telephone",
                    e.target.value
                  )
                }
                placeholder="+224..."
              />
            </div>

            <div className="form-champ">
              <label>Email</label>

              <input
                type="email"
                value={form.responsable_email}
                onChange={(e) =>
                  modifier(
                    "responsable_email",
                    e.target.value
                  )
                }
                placeholder="responsable@example.com"
              />
            </div>
          </div>
        </section>

        {/* =====================================================
            ADMIN LOCAL
        ====================================================== */}

        <section
          className="carte"
          style={{ marginTop: 20 }}
        >
          <div className="page-section-heading">
            <div>
              <span className="eyebrow">
                COMPTE D'ACCÈS
              </span>

              <h3>Créer l'administrateur de l'église</h3>

              <p>
                Le Bureau national peut créer le compte
                administrateur en même temps que l'église.
                Le compte sera automatiquement lié à cette
                église.
              </p>
            </div>
          </div>

          <label
            style={{
              display: "flex",
              gap: 10,
              alignItems: "center",
              marginBottom: 20,
            }}
          >
            <input
              type="checkbox"
              checked={form.creer_compte_admin}
              onChange={(e) =>
                modifier(
                  "creer_compte_admin",
                  e.target.checked
                )
              }
            />

            <span>
              Créer maintenant l'ADMIN_LOCAL
            </span>
          </label>

          {form.creer_compte_admin && (
            <div className="form-grille">
              <div className="form-champ">
                <label>Nom *</label>

                <input
                  value={form.admin_nom}
                  onChange={(e) =>
                    modifier(
                      "admin_nom",
                      e.target.value
                    )
                  }
                  placeholder="Nom"
                />
              </div>

              <div className="form-champ">
                <label>Prénom *</label>

                <input
                  value={form.admin_prenom}
                  onChange={(e) =>
                    modifier(
                      "admin_prenom",
                      e.target.value
                    )
                  }
                  placeholder="Prénom"
                />
              </div>

              <div className="form-champ">
                <label>Téléphone *</label>

                <input
                  value={form.admin_telephone}
                  onChange={(e) =>
                    modifier(
                      "admin_telephone",
                      e.target.value
                    )
                  }
                  placeholder="+224..."
                />
              </div>

              <div className="form-champ">
                <label>Email</label>

                <input
                  type="email"
                  value={form.admin_email}
                  onChange={(e) =>
                    modifier(
                      "admin_email",
                      e.target.value
                    )
                  }
                  placeholder="admin@example.com"
                />
              </div>

              <div className="form-champ">
                <label>Mot de passe *</label>

                <input
                  type="password"
                  value={form.admin_mot_de_passe}
                  onChange={(e) =>
                    modifier(
                      "admin_mot_de_passe",
                      e.target.value
                    )
                  }
                  placeholder="Mot de passe"
                />
              </div>

              <div className="form-champ">
                <label>
                  Confirmation du mot de passe *
                </label>

                <input
                  type="password"
                  value={form.admin_confirmation}
                  onChange={(e) =>
                    modifier(
                      "admin_confirmation",
                      e.target.value
                    )
                  }
                  placeholder="Confirmer le mot de passe"
                />
              </div>
            </div>
          )}

          {form.creer_compte_admin && (
            <div
              className="console-success"
              style={{ marginTop: 15 }}
            >
              <strong>ADMIN_LOCAL</strong>

              <br />

              Le rôle sera attribué automatiquement et
              le compte sera lié à l'église créée.

              <br />

              <small>
                L'activation effective du compte reste
                sous le contrôle du Bureau national.
              </small>
            </div>
          )}
        </section>

        {/* =====================================================
            MESSAGES
        ====================================================== */}

        {message && (
          <div
            className="console-success"
            style={{ marginTop: 20 }}
          >
            {message}
          </div>
        )}

        {erreur && (
          <div
            className="console-error"
            style={{ marginTop: 20 }}
          >
            {erreur}
          </div>
        )}

        {/* =====================================================
            RESULTAT
        ====================================================== */}

        {resultat && (
          <section
            className="carte"
            style={{ marginTop: 20 }}
          >
            <h3>Église créée</h3>

            <p>
              <strong>
                {resultat.nom}
              </strong>
            </p>

            {resultat.code && (
              <p>
                Code :{" "}
                <strong>{resultat.code}</strong>
              </p>
            )}

            {resultat.compte_admin && (
              <div
                className="console-success"
                style={{ marginTop: 15 }}
              >
                <strong>
                  Administrateur créé
                </strong>

                <br />

                Identifiant :{" "}
                <strong>
                  {resultat.compte_admin.identifiant}
                </strong>

                <br />

                Statut :{" "}
                {resultat.compte_admin.actif
                  ? "Actif"
                  : "En attente d'activation"}
              </div>
            )}
          </section>
        )}

        {/* =====================================================
            BOUTON
        ====================================================== */}

        <div
          style={{
            display: "flex",
            justifyContent: "flex-end",
            marginTop: 25,
          }}
        >
          <button
            type="submit"
            className="btn"
            disabled={creation}
          >
            {creation
              ? "Création en cours..."
              : "Créer l'église"}
          </button>
        </div>
      </form>

      {/* =====================================================
          MODALE AJOUT GEO
      ====================================================== */}

      {ajoutOuvert && (
        <div
          className="modale-fond"
          onClick={fermerAjout}
        >
          <div
            className="modale"
            onClick={(event) =>
              event.stopPropagation()
            }
            style={{
              maxWidth: 500,
              width: "100%",
            }}
          >
            <h3>
              Ajouter{" "}
              {ajoutOuvert === "region"
                ? "une région"
                : ajoutOuvert === "prefecture"
                  ? "une préfecture"
                  : ajoutOuvert === "district"
                    ? "un district"
                    : "une commune"}
            </h3>

            <p>
              Cette nouvelle donnée sera ajoutée au
              référentiel géographique national.
            </p>

            <div className="form-champ">
              <label htmlFor="nouveau-geo">
                Nom *
              </label>

              <input
                id="nouveau-geo"
                autoFocus
                value={nouveauNom}
                onChange={(e) =>
                  setNouveauNom(e.target.value)
                }
                placeholder="Saisissez le nom"
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    ajouterGeographie();
                  }
                }}
              />
            </div>

            {erreur && (
              <div
                className="console-error"
                style={{ marginTop: 10 }}
              >
                {erreur}
              </div>
            )}

            <div
              style={{
                display: "flex",
                gap: 10,
                justifyContent: "flex-end",
                marginTop: 20,
              }}
            >
              <button
                type="button"
                className="btn btn-secondaire"
                onClick={fermerAjout}
                disabled={ajoutChargement}
              >
                Annuler
              </button>

              <button
                type="button"
                className="btn"
                onClick={ajouterGeographie}
                disabled={
                  ajoutChargement ||
                  !nouveauNom.trim()
                }
              >
                {ajoutChargement
                  ? "Ajout..."
                  : "Ajouter"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
