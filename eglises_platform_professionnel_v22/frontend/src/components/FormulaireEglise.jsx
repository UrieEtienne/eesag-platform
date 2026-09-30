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

const extraireListe = (data) =>
  data?.results || data || [];

export default function FormulaireEglise({
  onFerme,
  onCree,
}) {
  const [regions, setRegions] = useState([]);
  const [prefectures, setPrefectures] = useState([]);
  const [districts, setDistricts] = useState([]);
  const [communes, setCommunes] = useState([]);

  const [form, setForm] = useState(initial);

  const [erreur, setErreur] = useState("");
  const [message, setMessage] = useState("");
  const [resultat, setResultat] = useState(null);

  const [chargement, setChargement] = useState(false);

  /* =========================================================
     CHARGEMENT DES RÉGIONS
  ========================================================= */

  useEffect(() => {
    chargerRegions();
  }, []);

  const chargerRegions = async () => {
    try {
      const response = await client.get("/geo/regions/");
      setRegions(extraireListe(response.data));
    } catch {
      setRegions([]);
    }
  };

  /* =========================================================
     RÉGION → PRÉFECTURES
  ========================================================= */

  useEffect(() => {
    if (!form.region) {
      setPrefectures([]);
      setDistricts([]);
      setCommunes([]);
      return;
    }

    chargerPrefectures(form.region);
  }, [form.region]);

  const chargerPrefectures = async (regionId) => {
    try {
      const response = await client.get(
        "/geo/prefectures/",
        {
          params: {
            region: regionId,
          },
        }
      );

      setPrefectures(
        extraireListe(response.data)
      );
    } catch {
      setPrefectures([]);
    }
  };

  /* =========================================================
     PRÉFECTURE → DISTRICTS
  ========================================================= */

  useEffect(() => {
    if (!form.prefecture) {
      setDistricts([]);
      setCommunes([]);
      return;
    }

    chargerDistricts(form.prefecture);
  }, [form.prefecture]);

  const chargerDistricts = async (prefectureId) => {
    try {
      const response = await client.get(
        "/geo/districts/",
        {
          params: {
            prefecture: prefectureId,
          },
        }
      );

      setDistricts(
        extraireListe(response.data)
      );
    } catch {
      setDistricts([]);
    }
  };

  /* =========================================================
     DISTRICT → COMMUNES
  ========================================================= */

  useEffect(() => {
    if (!form.district) {
      setCommunes([]);
      return;
    }

    chargerCommunes(form.district);
  }, [form.district]);

  const chargerCommunes = async (districtId) => {
    try {
      const response = await client.get(
        "/geo/communes/",
        {
          params: {
            district: districtId,
          },
        }
      );

      setCommunes(
        extraireListe(response.data)
      );
    } catch {
      setCommunes([]);
    }
  };

  /* =========================================================
     MODIFICATION FORMULAIRE
  ========================================================= */

  const modifier = (champ, valeur) => {
    setForm((ancien) => ({
      ...ancien,
      [champ]: valeur,
    }));
  };

  const changerRegion = (value) => {
    setForm((ancien) => ({
      ...ancien,
      region: value,
      prefecture: "",
      district: "",
      commune: "",
    }));

    setDistricts([]);
    setCommunes([]);
  };

  const changerPrefecture = (value) => {
    setForm((ancien) => ({
      ...ancien,
      prefecture: value,
      district: "",
      commune: "",
    }));

    setCommunes([]);
  };

  const changerDistrict = (value) => {
    setForm((ancien) => ({
      ...ancien,
      district: value,
      commune: "",
    }));
  };

  /* =========================================================
     AJOUT RAPIDE D'UNE LOCALITÉ
     
     Ces fonctions utilisent les endpoints géographiques
     existants. Si ton backend ne permet pas encore POST sur
     ces endpoints, il faudra également activer la création
     côté Django.
  ========================================================= */

  const ajouterRegion = async () => {
    const nom = window.prompt(
      "Nom de la nouvelle région :"
    );

    if (!nom?.trim()) return;

    try {
      const response = await client.post(
        "/geo/regions/",
        {
          nom: nom.trim(),
        }
      );

      const nouvelle = response.data;

      setRegions((liste) => [
        ...liste,
        nouvelle,
      ]);

      changerRegion(nouvelle.id);

      setMessage(
        `Région « ${nouvelle.nom} » ajoutée.`
      );
    } catch (error) {
      setErreur(
        extraireErreur(
          error,
          "Impossible d'ajouter la région."
        )
      );
    }
  };

  const ajouterPrefecture = async () => {
    if (!form.region) {
      setErreur(
        "Sélectionnez d'abord une région."
      );
      return;
    }

    const nom = window.prompt(
      "Nom de la nouvelle préfecture :"
    );

    if (!nom?.trim()) return;

    try {
      const response = await client.post(
        "/geo/prefectures/",
        {
          nom: nom.trim(),
          region: form.region,
        }
      );

      const nouvelle = response.data;

      setPrefectures((liste) => [
        ...liste,
        nouvelle,
      ]);

      changerPrefecture(nouvelle.id);

      setMessage(
        `Préfecture « ${nouvelle.nom} » ajoutée.`
      );
    } catch (error) {
      setErreur(
        extraireErreur(
          error,
          "Impossible d'ajouter la préfecture."
        )
      );
    }
  };

  const ajouterDistrict = async () => {
    if (!form.prefecture) {
      setErreur(
        "Sélectionnez d'abord une préfecture."
      );
      return;
    }

    const nom = window.prompt(
      "Nom du nouveau district :"
    );

    if (!nom?.trim()) return;

    try {
      const response = await client.post(
        "/geo/districts/",
        {
          nom: nom.trim(),
          prefecture: form.prefecture,
        }
      );

      const nouveau = response.data;

      setDistricts((liste) => [
        ...liste,
        nouveau,
      ]);

      changerDistrict(nouveau.id);

      setMessage(
        `District « ${nouveau.nom} » ajouté.`
      );
    } catch (error) {
      setErreur(
        extraireErreur(
          error,
          "Impossible d'ajouter le district."
        )
      );
    }
  };

  const ajouterCommune = async () => {
    if (!form.district) {
      setErreur(
        "Sélectionnez d'abord un district."
      );
      return;
    }

    const nom = window.prompt(
      "Nom de la nouvelle commune :"
    );

    if (!nom?.trim()) return;

    try {
      const response = await client.post(
        "/geo/communes/",
        {
          nom: nom.trim(),
          district: form.district,
        }
      );

      const nouvelle = response.data;

      setCommunes((liste) => [
        ...liste,
        nouvelle,
      ]);

      modifier("commune", nouvelle.id);

      setMessage(
        `Commune « ${nouvelle.nom} » ajoutée.`
      );
    } catch (error) {
      setErreur(
        extraireErreur(
          error,
          "Impossible d'ajouter la commune."
        )
      );
    }
  };

  /* =========================================================
     NORMALISATION TÉLÉPHONE
  ========================================================= */

  const normaliserNumero = (value) => {
    const raw = String(value || "")
      .trim()
      .replace(/[\s().-]/g, "");

    if (raw.startsWith("00")) {
      return "+" + raw.slice(2);
    }

    if (raw.startsWith("+")) {
      return (
        "+" +
        raw
          .slice(1)
          .replace(/\D/g, "")
      );
    }

    const digits = raw.replace(
      /\D/g,
      ""
    );

    if (
      digits.length === 9 &&
      digits.startsWith("6")
    ) {
      return "+224" + digits;
    }

    if (
      digits.startsWith("224") &&
      digits.length === 12
    ) {
      return "+" + digits;
    }

    return raw;
  };

  /* =========================================================
     VALIDATION
  ========================================================= */

  const valider = () => {
    if (!form.nom.trim()) {
      return "Le nom de l'église est obligatoire.";
    }

    if (!form.region) {
      return "La région est obligatoire.";
    }

    if (!form.prefecture) {
      return "La préfecture est obligatoire.";
    }

    if (!form.district) {
      return "Le district est obligatoire.";
    }

    if (!form.date_creation) {
      return "La date de fondation est obligatoire.";
    }

    if (!form.responsable_nom.trim()) {
      return "Le nom du responsable est obligatoire.";
    }

    if (form.creer_compte_admin) {
      if (!form.admin_nom.trim()) {
        return "Le nom de l'administrateur est obligatoire.";
      }

      if (!form.admin_prenom.trim()) {
        return "Le prénom de l'administrateur est obligatoire.";
      }

      if (!form.admin_telephone.trim()) {
        return "Le téléphone de l'administrateur est obligatoire.";
      }

      if (form.admin_mot_de_passe.length < 6) {
        return "Le mot de passe doit contenir au moins 6 caractères.";
      }

      if (
        form.admin_mot_de_passe !==
        form.admin_confirmation
      ) {
        return "Les mots de passe ne correspondent pas.";
      }
    }

    return "";
  };

  /* =========================================================
     CRÉATION ÉGLISE + ADMIN LOCAL
  ========================================================= */

  const soumettre = async (event) => {
    event.preventDefault();

    setErreur("");
    setMessage("");
    setChargement(true);

    try {
      const validation = valider();

      if (validation) {
        throw new Error(validation);
      }

      /*
       * IMPORTANT :
       * Aucun champ religion n'est envoyé.
       */

      const payload = {
        nom: form.nom.trim(),

        region: form.region,
        prefecture: form.prefecture,
        district: form.district,
        commune: form.commune || null,

        adresse_precise:
          form.adresse_precise.trim(),

        telephone: normaliserNumero(
          form.telephone
        ),

        email: form.email.trim(),

        date_creation:
          form.date_creation,

        responsable_nom:
          form.responsable_nom.trim(),

        responsable_telephone:
          normaliserNumero(
            form.responsable_telephone
          ),

        responsable_email:
          form.responsable_email.trim(),

        /*
         * Création du compte local directement
         * dans le même processus.
         */
        creer_compte_admin:
          form.creer_compte_admin,

        ...(form.creer_compte_admin
          ? {
              admin_nom:
                form.admin_nom.trim(),

              admin_prenom:
                form.admin_prenom.trim(),

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

              /*
               * Le compte est créé mais reste
               * inactif jusqu'à activation nationale.
               */
              admin_actif: false,
            }
          : {}),
      };

      const response = await client.post(
        "/eglises/",
        payload
      );

      setResultat(response.data);
    } catch (error) {
      setErreur(
        extraireErreur(
          error,
          "Impossible de créer l'église."
        )
      );
    } finally {
      setChargement(false);
    }
  };

  /* =========================================================
     ÉCRAN SUCCÈS
  ========================================================= */

  if (resultat) {
    const compte =
      resultat.compte_admin ||
      resultat.admin ||
      null;

    return (
      <div
        className="modale-fond"
        onClick={onFerme}
      >
        <div
          className="modale"
          onClick={(event) =>
            event.stopPropagation()
          }
        >
          <div className="success-box">
            <div className="success-icon">
              ✓
            </div>

            <h3>
              Église créée avec succès
            </h3>

            <p>
              <b>
                {resultat.nom ||
                  form.nom}
              </b>{" "}
              est maintenant enregistrée
              dans le réseau EESAG.
            </p>

            <div className="credential-box">
              <small>
                Code de l'église
              </small>

              <strong>
                {resultat.code || "—"}
              </strong>

              {compte && (
                <>
                  <small>
                    Administrateur local
                  </small>

                  <strong>
                    {compte.prenom ||
                      form.admin_prenom}{" "}
                    {compte.nom ||
                      form.admin_nom}
                  </strong>

                  <small>
                    Identifiant
                  </small>

                  <strong>
                    {compte.identifiant ||
                      "Généré par le serveur"}
                  </strong>

                  <small>
                    Église liée
                  </small>

                  <strong>
                    {resultat.nom ||
                      form.nom}
                  </strong>

                  <small>
                    État du compte
                  </small>

                  <strong>
                    {compte.actif
                      ? "Actif"
                      : "En attente d'activation"}
                  </strong>
                </>
              )}
            </div>

            {!compte &&
              form.creer_compte_admin && (
                <p className="console-error">
                  L'église a été créée, mais
                  le compte administrateur n'a
                  pas été retourné par le serveur.
                  Vérifie le serializer Django.
                </p>
              )}

            <button
              className="btn"
              type="button"
              onClick={() => {
                onCree?.(resultat);
                onFerme?.();
              }}
            >
              Fermer
            </button>
          </div>
        </div>
      </div>
    );
  }

  /* =========================================================
     FORMULAIRE
  ========================================================= */

  return (
    <div
      className="modale-fond"
      onClick={onFerme}
    >
      <div
        className="modale xl"
        onClick={(event) =>
          event.stopPropagation()
        }
      >
        <div className="section-header">
          <div>
            <span className="eyebrow">
              BUREAU NATIONAL
            </span>

            <h3>
              Créer une nouvelle église
            </h3>

            <p>
              L'église et son administrateur
              local peuvent être créés
              ensemble.
            </p>
          </div>
        </div>

        <div className="activation-note">
          <b>
            Processus de création
          </b>

          <small>
            L'église est créée avec son espace
            privé. Le compte ADMIN_LOCAL est
            automatiquement lié à cette église
            et reste inactif jusqu'à son
            activation par le Bureau national.
          </small>
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

        <form onSubmit={soumettre}>
          {/* =================================================
              ÉGLISE
          ================================================= */}

          <div className="form-section">
            <h4>
              Informations de l'église
            </h4>

            <div className="form-grid">
              <div className="form-champ">
                <label>
                  Nom de l'église *
                </label>

                <input
                  required
                  value={form.nom}
                  onChange={(event) =>
                    modifier(
                      "nom",
                      event.target.value
                    )
                  }
                  placeholder="Ex. EESAG Conakry Centre"
                />
              </div>

              <div className="form-champ">
                <label>
                  Région *
                </label>

                <div className="select-with-action">
                  <select
                    required
                    value={form.region}
                    onChange={(event) =>
                      changerRegion(
                        event.target.value
                      )
                    }
                  >
                    <option value="">
                      Sélectionner une région
                    </option>

                    {regions.map((item) => (
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
                    onClick={ajouterRegion}
                  >
                    + Ajouter
                  </button>
                </div>
              </div>

              <div className="form-champ">
                <label>
                  Préfecture *
                </label>

                <div className="select-with-action">
                  <select
                    required
                    disabled={!form.region}
                    value={
                      form.prefecture
                    }
                    onChange={(event) =>
                      changerPrefecture(
                        event.target.value
                      )
                    }
                  >
                    <option value="">
                      Sélectionner une préfecture
                    </option>

                    {prefectures.map(
                      (item) => (
                        <option
                          key={item.id}
                          value={item.id}
                        >
                          {item.nom}
                        </option>
                      )
                    )}
                  </select>

                  <button
                    type="button"
                    className="btn btn-secondaire"
                    disabled={!form.region}
                    onClick={
                      ajouterPrefecture
                    }
                  >
                    + Ajouter
                  </button>
                </div>
              </div>

              <div className="form-champ">
                <label>
                  District *
                </label>

                <div className="select-with-action">
                  <select
                    required
                    disabled={
                      !form.prefecture
                    }
                    value={
                      form.district
                    }
                    onChange={(event) =>
                      changerDistrict(
                        event.target.value
                      )
                    }
                  >
                    <option value="">
                      Sélectionner un district
                    </option>

                    {districts.map(
                      (item) => (
                        <option
                          key={item.id}
                          value={item.id}
                        >
                          {item.nom}
                        </option>
                      )
                    )}
                  </select>

                  <button
                    type="button"
                    className="btn btn-secondaire"
                    disabled={
                      !form.prefecture
                    }
                    onClick={
                      ajouterDistrict
                    }
                  >
                    + Ajouter
                  </button>
                </div>
              </div>

              <div className="form-champ">
                <label>
                  Commune
                </label>

                <div className="select-with-action">
                  <select
                    disabled={
                      !form.district
                    }
                    value={
                      form.commune
                    }
                    onChange={(event) =>
                      modifier(
                        "commune",
                        event.target.value
                      )
                    }
                  >
                    <option value="">
                      Sélectionner une commune
                    </option>

                    {communes.map(
                      (item) => (
                        <option
                          key={item.id}
                          value={item.id}
                        >
                          {item.nom}
                        </option>
                      )
                    )}
                  </select>

                  <button
                    type="button"
                    className="btn btn-secondaire"
                    disabled={
                      !form.district
                    }
                    onClick={
                      ajouterCommune
                    }
                  >
                    + Ajouter
                  </button>
                </div>
              </div>

              <div className="form-champ">
                <label>
                  Date de fondation *
                </label>

                <input
                  required
                  type="date"
                  value={
                    form.date_creation
                  }
                  onChange={(event) =>
                    modifier(
                      "date_creation",
                      event.target.value
                    )
                  }
                />
              </div>

              <div className="form-champ">
                <label>
                  Téléphone
                </label>

                <input
                  inputMode="tel"
                  value={
                    form.telephone
                  }
                  onChange={(event) =>
                    modifier(
                      "telephone",
                      event.target.value
                    )
                  }
                  placeholder="+224..."
                />
              </div>

              <div className="form-champ">
                <label>
                  Email
                </label>

                <input
                  type="email"
                  value={form.email}
                  onChange={(event) =>
                    modifier(
                      "email",
                      event.target.value
                    )
                  }
                />
              </div>
            </div>

            <div className="form-champ">
              <label>
                Adresse précise
              </label>

              <input
                value={
                  form.adresse_precise
                }
                onChange={(event) =>
                  modifier(
                    "adresse_precise",
                    event.target.value
                  )
                }
                placeholder="Adresse complète de l'église"
              />
            </div>
          </div>

          {/* =================================================
              RESPONSABLE
          ================================================= */}

          <div className="form-section">
            <h4>
              Responsable de l'église
            </h4>

            <p className="sous-titre">
              Ces informations permettent
              d'identifier le responsable
              de référence.
            </p>

            <div className="form-grid">
              <div className="form-champ">
                <label>
                  Nom du responsable *
                </label>

                <input
                  required
                  value={
                    form.responsable_nom
                  }
                  onChange={(event) =>
                    modifier(
                      "responsable_nom",
                      event.target.value
                    )
                  }
                />
              </div>

              <div className="form-champ">
                <label>
                  Téléphone
                </label>

                <input
                  inputMode="tel"
                  value={
                    form.responsable_telephone
                  }
                  onChange={(event) =>
                    modifier(
                      "responsable_telephone",
                      event.target.value
                    )
                  }
                  placeholder="+224..."
                />
              </div>

              <div className="form-champ">
                <label>
                  Email
                </label>

                <input
                  type="email"
                  value={
                    form.responsable_email
                  }
                  onChange={(event) =>
                    modifier(
                      "responsable_email",
                      event.target.value
                    )
                  }
                />
              </div>
            </div>
          </div>

          {/* =================================================
              ADMIN LOCAL
          ================================================= */}

          <div className="form-section admin-section">
            <h4>
              Administrateur de l'église
            </h4>

            <label className="checkbox-line">
              <input
                type="checkbox"
                checked={
                  form.creer_compte_admin
                }
                onChange={(event) =>
                  modifier(
                    "creer_compte_admin",
                    event.target.checked
                  )
                }
              />

              <span>
                <b>
                  Créer maintenant le compte
                  ADMIN_LOCAL
                </b>

                <small>
                  Le compte sera automatiquement
                  rattaché à cette église.
                </small>
              </span>
            </label>

            {form.creer_compte_admin && (
              <>
                <div className="form-grid">
                  <div className="form-champ">
                    <label>
                      Nom *
                    </label>

                    <input
                      required
                      value={
                        form.admin_nom
                      }
                      onChange={(event) =>
                        modifier(
                          "admin_nom",
                          event.target.value
                        )
                      }
                    />
                  </div>

                  <div className="form-champ">
                    <label>
                      Prénom *
                    </label>

                    <input
                      required
                      value={
                        form.admin_prenom
                      }
                      onChange={(event) =>
                        modifier(
                          "admin_prenom",
                          event.target.value
                        )
                      }
                    />
                  </div>

                  <div className="form-champ">
                    <label>
                      Téléphone *
                    </label>

                    <input
                      required
                      inputMode="tel"
                      value={
                        form.admin_telephone
                      }
                      onChange={(event) =>
                        modifier(
                          "admin_telephone",
                          event.target.value
                        )
                      }
                      placeholder="+224626483701"
                    />
                  </div>

                  <div className="form-champ">
                    <label>
                      Email
                    </label>

                    <input
                      type="email"
                      value={
                        form.admin_email
                      }
                      onChange={(event) =>
                        modifier(
                          "admin_email",
                          event.target.value
                        )
                      }
                    />
                  </div>

                  <div className="form-champ">
                    <label>
                      Mot de passe *
                    </label>

                    <input
                      required
                      minLength={6}
                      type="password"
                      value={
                        form.admin_mot_de_passe
                      }
                      onChange={(event) =>
                        modifier(
                          "admin_mot_de_passe",
                          event.target.value
                        )
                      }
                    />
                  </div>

                  <div className="form-champ">
                    <label>
                      Confirmation *
                    </label>

                    <input
                      required
                      minLength={6}
                      type="password"
                      value={
                        form.admin_confirmation
                      }
                      onChange={(event) =>
                        modifier(
                          "admin_confirmation",
                          event.target.value
                        )
                      }
                    />
                  </div>
                </div>

                <div className="activation-note">
                  <b>
                    Liaison automatique
                  </b>

                  <small>
                    Cet administrateur sera
                    automatiquement associé à
                    l'église créée. Aucun choix
                    d'église supplémentaire ne
                    sera demandé.
                  </small>
                </div>
              </>
            )}
          </div>

          {/* =================================================
              ACTIONS
          ================================================= */}

          <div className="modal-actions">
            <button
              className="btn"
              type="submit"
              disabled={chargement}
            >
              {chargement
                ? "Création en cours..."
                : "Créer l'église"}
            </button>

            <button
              className="btn btn-secondaire"
              type="button"
              disabled={chargement}
              onClick={onFerme}
            >
              Annuler
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

/* ===========================================================
   ERREURS API
=========================================================== */

function extraireErreur(
  error,
  fallback
) {
  const data = error?.response?.data;

  if (!data) {
    return (
      error?.message ||
      fallback
    );
  }

  if (typeof data === "string") {
    return data;
  }

  if (data.detail) {
    return String(data.detail);
  }

  const messages = [];

  Object.entries(data).forEach(
    ([champ, valeur]) => {
      if (Array.isArray(valeur)) {
        messages.push(
          `${champ} : ${valeur.join(", ")}`
        );
      } else if (
        typeof valeur === "object" &&
        valeur !== null
      ) {
        messages.push(
          `${champ} : ${JSON.stringify(
            valeur
          )}`
        );
      } else {
        messages.push(
          `${champ} : ${String(valeur)}`
        );
      }
    }
  );

  return (
    messages.join(" ") ||
    fallback
  );
}