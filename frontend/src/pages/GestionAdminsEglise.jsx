import { useEffect, useMemo, useState } from "react";
import client from "../api/client";
import { useAuth } from "../context/AuthContext";
import { PERMISSIONS_ADMIN_DELEGUE } from "../config/optionsEgliseLocale";
import "../styles/eglise-locale.css";

const EMPTY = {
  nom: "",
  prenom: "",
  telephone: "",
  email: "",
  mot_de_passe: "",
  confirmation_mot_de_passe: "",
  photo: null,
  role: "ADMIN_LOCAL",
  permissions: [],
};

const ROLES_DISPONIBLES = [
  {
    value: "ADMIN_LOCAL",
    label: "Administrateur local",
    description:
      "Gestionnaire de l'administration de l'église.",
  },
  {
    value: "PASTEUR",
    label: "Pasteur",
    description:
      "Responsable pastoral de l'église.",
  },
  {
    value: "RESPONSABLE_DEPARTEMENT",
    label: "Responsable de département",
    description:
      "Responsable d'un département de l'église.",
  },
  {
    value: "MEMBRE",
    label: "Membre",
    description:
      "Compte membre avec accès limité.",
  },
];

/*
 * ============================================================
 * OUTILS
 * ============================================================
 */

const normaliser = (value) =>
  String(value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toUpperCase()
    .replace(/[^A-Z0-9]+/g, "_")
    .replace(/^_|_$/g, "");

const extraireIdEglise = (eglise) => {
  if (!eglise) {
    return null;
  }

  if (typeof eglise === "object") {
    return (
      eglise.id ||
      eglise.pk ||
      eglise.code ||
      null
    );
  }

  return eglise;
};

const extraireNomEglise = (utilisateur) => {
  if (!utilisateur) {
    return "l'église";
  }

  if (utilisateur.eglise_nom) {
    return utilisateur.eglise_nom;
  }

  if (typeof utilisateur.eglise === "object") {
    return (
      utilisateur.eglise.nom ||
      utilisateur.eglise.name ||
      utilisateur.eglise.libelle ||
      "l'église"
    );
  }

  return "l'église";
};

const extraireNomComplet = (utilisateur) => {
  if (!utilisateur) {
    return "";
  }

  return (
    String(utilisateur.prenom || "") +
    " " +
    String(utilisateur.nom || "")
  ).trim();
};

const obtenirNomFichier = (fichier) => {
  if (!fichier) {
    return "";
  }

  return fichier.name || "photo";
};

const obtenirRoleLabel = (role) => {
  const roleNormalise = String(
    role || ""
  ).toUpperCase();

  const trouve = ROLES_DISPONIBLES.find(
    (item) =>
      item.value === roleNormalise
  );

  return (
    trouve?.label ||
    role ||
    "Rôle non défini"
  );
};

/*
 * ============================================================
 * EXTRACTION ERREUR DJANGO / DRF
 * ============================================================
 */

const extraireMessageErreur = (error) => {
  const data =
    error?.response?.data ||
    error?.data ||
    error;

  if (!data) {
    return "Impossible de créer le compte.";
  }

  if (typeof data === "string") {
    return data;
  }

  if (data.detail) {
    return String(data.detail);
  }

  if (data.message) {
    return String(data.message);
  }

  if (data.error) {
    return String(data.error);
  }

  if (data.non_field_errors) {
    if (Array.isArray(data.non_field_errors)) {
      return data.non_field_errors.join(" | ");
    }

    return String(data.non_field_errors);
  }

  if (typeof data === "object") {
    const erreurs = [];

    Object.entries(data).forEach(
      ([champ, valeur]) => {
        if (Array.isArray(valeur)) {
          erreurs.push(
            `${champ} : ${valeur.join(", ")}`
          );
          return;
        }

        if (
          valeur &&
          typeof valeur === "object"
        ) {
          try {
            erreurs.push(
              `${champ} : ${JSON.stringify(
                valeur
              )}`
            );
          } catch {
            erreurs.push(
              `${champ} : erreur inconnue`
            );
          }

          return;
        }

        erreurs.push(
          `${champ} : ${String(valeur)}`
        );
      }
    );

    if (erreurs.length) {
      return erreurs.join(" | ");
    }
  }

  return (
    error?.message ||
    "Impossible de créer le compte."
  );
};

export default function GestionAdminsEglise() {
  const auth = useAuth();

  const utilisateur =
    auth?.utilisateur || null;

  const estAdminLocalContext =
    Boolean(auth?.estAdminLocal);

  const roleUtilisateur = String(
    utilisateur?.role || ""
  ).toUpperCase();

  const estAdminLocal =
    estAdminLocalContext ||
    roleUtilisateur === "ADMIN_LOCAL";

  const egliseId = useMemo(
    () =>
      extraireIdEglise(
        utilisateur?.eglise
      ),
    [utilisateur?.eglise]
  );

  const egliseNom = useMemo(
    () =>
      extraireNomEglise(
        utilisateur
      ),
    [utilisateur]
  );

  const nomAdministrateurConnecte =
    useMemo(
      () =>
        extraireNomComplet(
          utilisateur
        ),
      [utilisateur]
    );

  /*
   * ============================================================
   * ÉTATS
   * ============================================================
   */

  const [admins, setAdmins] =
    useState([]);

  const [permissionsApi, setPermissionsApi] =
    useState([]);

  const [form, setForm] =
    useState({
      ...EMPTY,
      permissions: [],
    });

  const [photoApercu, setPhotoApercu] =
    useState("");

  const [identifiantGenere, setIdentifiantGenere] =
    useState("");

  const [ouvert, setOuvert] =
    useState(false);

  const [chargement, setChargement] =
    useState(true);

  const [creationEnCours, setCreationEnCours] =
    useState(false);

  const [erreur, setErreur] =
    useState("");

  const [message, setMessage] =
    useState("");

  const [creationResultat, setCreationResultat] =
    useState(null);

  const peutAdministrer =
    estAdminLocal &&
    Boolean(egliseId);

  /*
   * ============================================================
   * CHARGEMENT
   * ============================================================
   */

  const charger = async () => {
    if (!estAdminLocal || !egliseId) {
      setChargement(false);
      return;
    }

    setChargement(true);
    setErreur("");

    try {
      const [
        utilisateursResponse,
        permissionsResponse,
      ] = await Promise.all([
        client.get("/utilisateurs/", {
          params: {
            role: "ADMIN_LOCAL",
            eglise: egliseId,
          },
        }),

        client.get(
          "/permissions-eglise/"
        ),
      ]);

      const utilisateurs =
        utilisateursResponse?.data?.results ??
        utilisateursResponse?.data ??
        utilisateursResponse?.results ??
        utilisateursResponse ??
        [];

      const permissions =
        permissionsResponse?.data?.results ??
        permissionsResponse?.data ??
        permissionsResponse?.results ??
        permissionsResponse ??
        [];

      setAdmins(
        Array.isArray(utilisateurs)
          ? utilisateurs
          : []
      );

      setPermissionsApi(
        Array.isArray(permissions)
          ? permissions
          : []
      );
    } catch (error) {
      console.error(
        "Erreur chargement administration église :",
        error
      );

      setErreur(
        extraireMessageErreur(error)
      );
    } finally {
      setChargement(false);
    }
  };

  useEffect(() => {
    charger();
  }, [
    estAdminLocal,
    egliseId,
  ]);

  /*
   * ============================================================
   * PERMISSIONS
   * ============================================================
   */

  const permissionsDisponibles =
    useMemo(() => {
      if (
        !Array.isArray(
          PERMISSIONS_ADMIN_DELEGUE
        )
      ) {
        return [];
      }

      return PERMISSIONS_ADMIN_DELEGUE.map(
        (definition) => {
          const codeDefinition =
            normaliser(
              definition.code
            );

          const apiPermission =
            permissionsApi.find(
              (permission) => {
                const codeApi =
                  normaliser(
                    permission?.code ||
                      permission?.nom ||
                      permission?.slug ||
                      permission?.libelle ||
                      ""
                  );

                if (
                  !codeApi ||
                  !codeDefinition
                ) {
                  return false;
                }

                return (
                  codeApi ===
                    codeDefinition ||
                  codeApi.includes(
                    codeDefinition
                  ) ||
                  codeDefinition.includes(
                    codeApi
                  )
                );
              }
            );

          return {
            ...definition,
            id:
              apiPermission?.id ||
              null,
            api:
              apiPermission ||
              null,
          };
        }
      );
    }, [permissionsApi]);

  const permissionsSelectionnees =
    useMemo(
      () =>
        new Set(
          form.permissions || []
        ),
      [form.permissions]
    );

  /*
   * ============================================================
   * IDENTIFIANT — APERÇU
   * ============================================================
   */

  const apercuIdentifiant =
    useMemo(() => {
      const prenom =
        normaliser(
          form.prenom
        );

      const nom =
        normaliser(
          form.nom
        );

      if (!prenom && !nom) {
        return "";
      }

      if (prenom && nom) {
        return (
          prenom.toLowerCase() +
          "." +
          nom.toLowerCase()
        );
      }

      return (
        prenom ||
        nom
      ).toLowerCase();
    }, [
      form.prenom,
      form.nom,
    ]);

  /*
   * ============================================================
   * FORMULAIRE
   * ============================================================
   */

  const modifierChamp = (
    champ,
    valeur
  ) => {
    setForm((ancien) => ({
      ...ancien,
      [champ]: valeur,
    }));

    setErreur("");
  };

  const changerPhoto = (event) => {
    const fichier =
      event.target.files &&
      event.target.files[0]
        ? event.target.files[0]
        : null;

    if (!fichier) {
      modifierChamp(
        "photo",
        null
      );

      setPhotoApercu("");

      return;
    }

    if (
      !fichier.type.startsWith(
        "image/"
      )
    ) {
      setErreur(
        "Veuillez sélectionner une image valide."
      );

      event.target.value = "";

      return;
    }

    if (
      fichier.size >
      5 * 1024 * 1024
    ) {
      setErreur(
        "La photo ne doit pas dépasser 5 Mo."
      );

      event.target.value = "";

      return;
    }

    modifierChamp(
      "photo",
      fichier
    );

    const lecteur =
      new FileReader();

    lecteur.onload = (
      resultat
    ) => {
      setPhotoApercu(
        resultat.target?.result ||
          ""
      );
    };

    lecteur.readAsDataURL(
      fichier
    );
  };

  const supprimerPhoto = () => {
    setForm((ancien) => ({
      ...ancien,
      photo: null,
    }));

    setPhotoApercu("");

    const input =
      document.getElementById(
        "photo-administrateur"
      );

    if (input) {
      input.value = "";
    }
  };

  const basculerPermission = (
    permission
  ) => {
    if (!permission?.id) {
      return;
    }

    setForm((ancien) => {
      const permissionsActuelles =
        Array.isArray(
          ancien.permissions
        )
          ? ancien.permissions
          : [];

      const dejaSelectionnee =
        permissionsActuelles.includes(
          permission.id
        );

      return {
        ...ancien,

        permissions:
          dejaSelectionnee
            ? permissionsActuelles.filter(
                (id) =>
                  id !==
                  permission.id
              )
            : [
                ...permissionsActuelles,
                permission.id,
              ],
      };
    });

    setErreur("");
  };

  /*
   * ============================================================
   * OUVERTURE / FERMETURE
   * ============================================================
   */

  const ouvrirModal = () => {
    setErreur("");
    setMessage("");
    setCreationResultat(null);

    setForm({
      ...EMPTY,
      role: "ADMIN_LOCAL",
      permissions: [],
    });

    setPhotoApercu("");
    setIdentifiantGenere("");

    setOuvert(true);
  };

  const fermerModal = () => {
    if (creationEnCours) {
      return;
    }

    setOuvert(false);

    setForm({
      ...EMPTY,
      role: "ADMIN_LOCAL",
      permissions: [],
    });

    setPhotoApercu("");
    setIdentifiantGenere("");
    setErreur("");
  };

  /*
   * ============================================================
   * CRÉATION
   * ============================================================
   */

  const creer = async (event) => {
    event.preventDefault();

    setErreur("");
    setMessage("");
    setCreationResultat(null);

    const nom =
      form.nom.trim();

    const prenom =
      form.prenom.trim();

    const telephone =
      form.telephone.trim();

    const email =
      form.email.trim();

    const role =
      String(
        form.role || ""
      ).trim().toUpperCase();

    /*
     * ----------------------------------------------------------
     * VALIDATION
     * ----------------------------------------------------------
     */

    if (!nom) {
      setErreur(
        "Le nom est obligatoire."
      );
      return;
    }

    if (!prenom) {
      setErreur(
        "Le prénom est obligatoire."
      );
      return;
    }

    if (!telephone) {
      setErreur(
        "Le numéro de téléphone est obligatoire."
      );
      return;
    }

    if (
      !ROLES_DISPONIBLES.some(
        (item) =>
          item.value === role
      )
    ) {
      setErreur(
        "Veuillez sélectionner un rôle valide."
      );
      return;
    }

    if (!form.mot_de_passe) {
      setErreur(
        "Le mot de passe est obligatoire."
      );
      return;
    }

    if (
      form.mot_de_passe.length <
      8
    ) {
      setErreur(
        "Le mot de passe doit contenir au moins 8 caractères."
      );
      return;
    }

    if (
      form.mot_de_passe !==
      form.confirmation_mot_de_passe
    ) {
      setErreur(
        "Les deux mots de passe ne correspondent pas."
      );
      return;
    }

    if (!egliseId) {
      setErreur(
        "Impossible de déterminer l'église du compte."
      );
      return;
    }

    if (
      !Array.isArray(
        form.permissions
      ) ||
      !form.permissions.length
    ) {
      setErreur(
        "Sélectionnez au moins une permission."
      );
      return;
    }

    setCreationEnCours(true);

    try {
      /*
       * ========================================================
       * FORMDATA
       * ========================================================
       */

      const donnees =
        new FormData();

      donnees.append(
        "nom",
        nom
      );

      donnees.append(
        "prenom",
        prenom
      );

      donnees.append(
        "telephone",
        telephone
      );

      if (email) {
        donnees.append(
          "email",
          email
        );
      }

      donnees.append(
        "mot_de_passe",
        form.mot_de_passe
      );

      donnees.append(
        "role",
        role
      );

      donnees.append(
        "eglise",
        String(egliseId)
      );

      donnees.append(
        "actif",
        "true"
      );

      /*
       * PHOTO
       */

      if (form.photo) {
        donnees.append(
          "photo",
          form.photo,
          obtenirNomFichier(
            form.photo
          )
        );
      }

      /*
       * DEBUG
       */

      console.log(
        "Création utilisateur :",
        {
          nom,
          prenom,
          telephone,
          email,
          role,
          eglise: egliseId,
          permissions:
            form.permissions,
          photo:
            Boolean(form.photo),
        }
      );

      /*
       * ========================================================
       * CRÉATION UTILISATEUR
       * ========================================================
       */

      const utilisateurResponse =
        await client.post(
          "/utilisateurs/",
          donnees
        );

      /*
       * Le client EESAG peut retourner :
       *
       * 1. directement les données JSON
       * 2. un objet contenant .data
       */

      const nouvelUtilisateur =
        utilisateurResponse?.data ||
        utilisateurResponse ||
        {};

      console.log(
        "Réponse création utilisateur :",
        nouvelUtilisateur
      );

      /*
       * ========================================================
       * ID INTERNE DU COMPTE
       * ========================================================
       */

      const nouvelUtilisateurId =
        nouvelUtilisateur?.id ||
        nouvelUtilisateur?.utilisateur?.id;

      /*
       * ========================================================
       * IDENTIFIANT DE CONNEXION
       * ========================================================
       */

      const nouvelIdentifiant =
        nouvelUtilisateur?.identifiant ||
        nouvelUtilisateur?.utilisateur?.identifiant ||
        nouvelUtilisateur?.username ||
        nouvelUtilisateur?.userName ||
        "";

      /*
       * Le backend EESAG doit retourner au minimum :
       *
       * identifiant
       * utilisateur.id
       */

      if (
        !nouvelUtilisateurId ||
        !nouvelIdentifiant
      ) {
        console.error(
          "Réponse serveur inattendue :",
          nouvelUtilisateur
        );

        throw new Error(
          "Le serveur n'a pas retourné les informations du nouveau compte."
        );
      }

      /*
       * Conserver l'identifiant généré.
       */

      setIdentifiantGenere(
        nouvelIdentifiant
      );

      /*
       * ========================================================
       * PERMISSIONS
       * ========================================================
       */

      try {
        await client.post(
          "/delegations-eglise/",
          {
            utilisateur:
              nouvelUtilisateurId,

            permissions:
              form.permissions,

            actif: true,
          }
        );
      } catch (permissionError) {
        console.error(
          "Erreur attribution permissions :",
          permissionError
        );

        throw new Error(
          "Le compte a été créé, mais les permissions n'ont pas pu être attribuées : " +
            extraireMessageErreur(
              permissionError
            )
        );
      }

      /*
       * ========================================================
       * SUCCÈS
       * ========================================================
       */

      const roleLabel =
        obtenirRoleLabel(
          role
        );

      setCreationResultat({
        identifiant: nouvelIdentifiant,
        nom: `${prenom} ${nom}`,
        role: roleLabel,
        eglise: egliseNom,
      });

      setMessage(
        "Le compte a été créé avec succès."
      );

      /*
       * Réinitialisation du formulaire.
       */

      setForm({
        ...EMPTY,
        role: "ADMIN_LOCAL",
        permissions: [],
      });

      setPhotoApercu("");

      /*
       * Recharger la liste.
       */

      await charger();

    } catch (error) {
      console.error(
        "Erreur création administrateur local :",
        error
      );

      console.error(
        "Réponse HTTP :",
        error?.response?.data
      );

      console.error(
        "Statut HTTP :",
        error?.response?.status
      );

      setErreur(
        extraireMessageErreur(
          error
        )
      );

    } finally {
      setCreationEnCours(false);
    }
  };

  /*
   * ============================================================
   * ACCÈS
   * ============================================================
   */

  if (!utilisateur) {
    return (
      <div className="page-admin-eglise">
        <section className="carte">
          <h2>
            Administration de l'église
          </h2>

          <p className="sous-titre">
            Chargement du compte utilisateur…
          </p>
        </section>
      </div>
    );
  }

  if (!estAdminLocal) {
    return (
      <div className="page-admin-eglise">
        <section className="carte">
          <span className="eyebrow">
            ACCÈS ADMINISTRATION
          </span>

          <h2>
            Accès réservé à l'administrateur local
          </h2>

          <p className="sous-titre">
            Cette page permet de créer et gérer
            les comptes utilisateurs de cette
            église.
          </p>

          <p>
            Rôle actuellement détecté :{" "}
            <strong>
              {utilisateur.role ||
                "non défini"}
            </strong>
          </p>
        </section>
      </div>
    );
  }

  if (!egliseId) {
    return (
      <div className="page-admin-eglise">
        <section className="carte">
          <span className="eyebrow">
            CONFIGURATION DU COMPTE
          </span>

          <h2>
            Aucune église n'est rattachée à ce compte
          </h2>

          <p className="sous-titre">
            Un administrateur local doit être
            rattaché à une église avant de pouvoir
            gérer ses utilisateurs.
          </p>
        </section>
      </div>
    );
  }

  if (!peutAdministrer) {
    return (
      <div className="page-admin-eglise">
        <section className="carte">
          <h2>
            Administration locale indisponible
          </h2>

          <p className="sous-titre">
            Vérifiez le rattachement de votre
            compte à une église.
          </p>
        </section>
      </div>
    );
  }

  /*
   * ============================================================
   * PAGE PRINCIPALE
   * ============================================================
   */

  return (
    <div className="page-admin-eglise">

      <div className="page-hero">

        <div>
          <span className="eyebrow">
            ADMINISTRATION DE L'ÉGLISE
          </span>

          <h1>
            Administrateurs de l'église
          </h1>

          <p>
            Gérez les comptes utilisateurs de{" "}
            <strong>
              {egliseNom}
            </strong>.
          </p>
        </div>

        <button
          type="button"
          className="btn"
          onClick={ouvrirModal}
        >
          ＋ Nouvel utilisateur
        </button>

      </div>

      {message && (
        <div className="console-success">
          {message}
        </div>
      )}

      {creationResultat && (
        <section className="carte creation-success-card">

          <div className="section-header">

            <div>
              <span className="eyebrow">
                COMPTE CRÉÉ
              </span>

              <h3>
                Identifiant de connexion
              </h3>
            </div>

          </div>

          <div className="creation-resultat">

            <div>
              <span>
                Nom
              </span>

              <strong>
                {creationResultat.nom}
              </strong>
            </div>

            <div>
              <span>
                Rôle
              </span>

              <strong>
                {creationResultat.role}
              </strong>
            </div>

            <div>
              <span>
                Église
              </span>

              <strong>
                {creationResultat.eglise}
              </strong>
            </div>

            <div className="identifiant-resultat">

              <span>
                Identifiant de connexion
              </span>

              <strong>
                {creationResultat.identifiant}
              </strong>

            </div>

          </div>

          <p className="form-help">
            Conservez cet identifiant pour permettre
            au nouvel utilisateur de se connecter.
            Le mot de passe choisi lors de la création
            n'est pas affiché ici.
          </p>

          <button
            type="button"
            className="btn btn-secondaire"
            onClick={() =>
              setCreationResultat(null)
            }
          >
            Fermer le résultat
          </button>

        </section>
      )}

      {erreur && !ouvert && (
        <div className="console-error">
          {erreur}
        </div>
      )}

      <section className="carte">

        <div className="section-header">

          <div>
            <span className="eyebrow">
              COMPTE ACTUEL
            </span>

            <h3>
              Administrateur connecté
            </h3>
          </div>

          <span className="scope-badge">
            Église : {egliseNom}
          </span>

        </div>

        <p>
          <strong>
            {nomAdministrateurConnecte ||
              utilisateur.identifiant ||
              "Administrateur"}
          </strong>
        </p>

        <p className="sous-titre">
          Vous pouvez créer des comptes utilisateurs
          pour cette église selon les permissions
          qui vous sont accordées.
        </p>

      </section>

      <section className="carte">

        <div className="section-header">

          <div>
            <span className="eyebrow">
              ADMINISTRATION LOCALE
            </span>

            <h3>
              Utilisateurs de {egliseNom}
            </h3>
          </div>

          <span className="scope-badge">
            Périmètre : cette église
          </span>

        </div>

        {chargement ? (
          <p className="sous-titre">
            Chargement des utilisateurs…
          </p>
        ) : (
          <div className="table-wrap">

            <table>

              <thead>
                <tr>
                  <th>
                    Photo
                  </th>

                  <th>
                    Identifiant
                  </th>

                  <th>
                    Nom complet
                  </th>

                  <th>
                    Téléphone
                  </th>

                  <th>
                    Email
                  </th>

                  <th>
                    État
                  </th>

                  <th>
                    Rôle
                  </th>
                </tr>
              </thead>

              <tbody>

                {admins.map(
                  (admin) => (
                    <tr key={admin.id}>

                      <td>
                        {admin.photo ? (
                          <img
                            src={admin.photo}
                            alt={
                              (
                                String(
                                  admin.prenom ||
                                    ""
                                ) +
                                " " +
                                String(
                                  admin.nom ||
                                    ""
                                )
                              ).trim()
                            }
                            className="admin-avatar"
                          />
                        ) : (
                          <div className="admin-avatar admin-avatar-placeholder">
                            {String(
                              admin.prenom ||
                                admin.nom ||
                                "A"
                            )
                              .charAt(0)
                              .toUpperCase()}
                          </div>
                        )}
                      </td>

                      <td>
                        <span className="code-pill">
                          {admin.identifiant ||
                            admin.username ||
                            "—"}
                        </span>
                      </td>

                      <td>
                        <b>
                          {admin.prenom ||
                            ""}{" "}
                          {admin.nom ||
                            ""}
                        </b>
                      </td>

                      <td>
                        {admin.telephone ||
                          "—"}
                      </td>

                      <td>
                        {admin.email ||
                          "—"}
                      </td>

                      <td>
                        {admin.actif ? (
                          <span className="status-active">
                            Actif
                          </span>
                        ) : (
                          <span className="status-off">
                            Désactivé
                          </span>
                        )}
                      </td>

                      <td>
                        <span className="code-pill">
                          {obtenirRoleLabel(
                            admin.role
                          )}
                        </span>
                      </td>

                    </tr>
                  )
                )}

              </tbody>

            </table>

            {!admins.length && (
              <div className="empty-state">
                Aucun utilisateur enregistré
                pour cette église.
              </div>
            )}

          </div>
        )}

      </section>

      {ouvert && (
        <div
          className="modale-fond"
          onClick={fermerModal}
        >

          <div
            className="modale admin-modal"
            onClick={(event) =>
              event.stopPropagation()
            }
          >

            <div className="modal-header">

              <div>

                <span className="eyebrow">
                  NOUVEL UTILISATEUR
                </span>

                <h3>
                  Créer un utilisateur
                </h3>

                <p className="sous-titre">
                  Le nouveau compte sera rattaché à{" "}
                  <strong>
                    {egliseNom}
                  </strong>.
                </p>

              </div>

              <button
                type="button"
                className="modal-close"
                onClick={fermerModal}
                disabled={
                  creationEnCours
                }
                aria-label="Fermer"
              >
                ×
              </button>

            </div>

            {erreur && (
              <div className="console-error">
                {erreur}
              </div>
            )}

            <form onSubmit={creer}>

              {/* ==================================================
                  1 — PHOTO
                  ================================================== */}

              <div className="form-section">

                <h4>
                  1. Photo de profil
                </h4>

                <div className="photo-upload-zone">

                  <div className="photo-profile-preview">

                    {photoApercu ? (
                      <img
                        src={photoApercu}
                        alt="Photo de profil"
                        className="photo-profile-image"
                      />
                    ) : (
                      <div className="photo-profile-placeholder">
                        <span>
                          👤
                        </span>
                      </div>
                    )}

                  </div>

                  <div className="photo-upload-actions">

                    <label
                      htmlFor="photo-administrateur"
                      className="btn"
                    >
                      📷 Choisir une photo
                    </label>

                    <input
                      id="photo-administrateur"
                      type="file"
                      accept="image/jpeg,image/png,image/webp"
                      onChange={
                        changerPhoto
                      }
                      hidden
                    />

                    {form.photo && (
                      <button
                        type="button"
                        className="btn btn-secondaire"
                        onClick={
                          supprimerPhoto
                        }
                      >
                        Supprimer
                      </button>
                    )}

                    <small>
                      Photo de profil — JPG,
                      PNG ou WEBP. Maximum
                      5 Mo.
                    </small>

                    {form.photo && (
                      <small>
                        {obtenirNomFichier(
                          form.photo
                        )}
                      </small>
                    )}

                  </div>

                </div>

              </div>

              {/* ==================================================
                  2 — IDENTITÉ
                  ================================================== */}

              <div className="form-section">

                <h4>
                  2. Informations personnelles
                </h4>

                <div className="form-grid">

                  <div className="form-champ">

                    <label htmlFor="nom">
                      Nom *
                    </label>

                    <input
                      id="nom"
                      required
                      autoComplete="family-name"
                      value={form.nom}
                      onChange={(event) =>
                        modifierChamp(
                          "nom",
                          event.target.value
                        )
                      }
                      placeholder="Ex. CAMARA"
                    />

                  </div>

                  <div className="form-champ">

                    <label htmlFor="prenom">
                      Prénom *
                    </label>

                    <input
                      id="prenom"
                      required
                      autoComplete="given-name"
                      value={form.prenom}
                      onChange={(event) =>
                        modifierChamp(
                          "prenom",
                          event.target.value
                        )
                      }
                      placeholder="Ex. Mohamed"
                    />

                  </div>

                  <div className="form-champ">

                    <label htmlFor="telephone">
                      Téléphone *
                    </label>

                    <input
                      id="telephone"
                      required
                      type="tel"
                      autoComplete="tel"
                      value={
                        form.telephone
                      }
                      onChange={(event) =>
                        modifierChamp(
                          "telephone",
                          event.target.value
                        )
                      }
                      placeholder="+224 6XX XX XX XX"
                    />

                  </div>

                  <div className="form-champ">

                    <label htmlFor="email">
                      Adresse email
                    </label>

                    <input
                      id="email"
                      type="email"
                      autoComplete="email"
                      value={form.email}
                      onChange={(event) =>
                        modifierChamp(
                          "email",
                          event.target.value
                        )
                      }
                      placeholder="adresse@email.com"
                    />

                  </div>

                </div>

              </div>

              {/* ==================================================
                  3 — IDENTIFIANT
                  ================================================== */}

              <div className="form-section">

                <h4>
                  3. Identifiant de connexion
                </h4>

                <div className="identifiant-auto">

                  <div>

                    <span className="identifiant-label">
                      Aperçu de l'identifiant
                    </span>

                    <strong>
                      {apercuIdentifiant ||
                        "Sera généré automatiquement"}
                    </strong>

                  </div>

                  <span className="auto-badge">
                    SERVEUR
                  </span>

                </div>

                <small className="form-help">
                  L'identifiant définitif est généré
                  par le serveur après validation de
                  la création. Il sera affiché après
                  création du compte.
                </small>

              </div>

              {/* ==================================================
                  4 — MOT DE PASSE
                  ================================================== */}

              <div className="form-section">

                <h4>
                  4. Sécurité du compte
                </h4>

                <div className="form-grid">

                  <div className="form-champ">

                    <label htmlFor="mot_de_passe">
                      Mot de passe *
                    </label>

                    <input
                      id="mot_de_passe"
                      required
                      type="password"
                      autoComplete="new-password"
                      minLength={8}
                      value={
                        form.mot_de_passe
                      }
                      onChange={(event) =>
                        modifierChamp(
                          "mot_de_passe",
                          event.target.value
                        )
                      }
                      placeholder="Minimum 8 caractères"
                    />

                    <small>
                      Minimum 8 caractères.
                    </small>

                  </div>

                  <div className="form-champ">

                    <label htmlFor="confirmation_mot_de_passe">
                      Confirmer le mot de passe *
                    </label>

                    <input
                      id="confirmation_mot_de_passe"
                      required
                      type="password"
                      autoComplete="new-password"
                      minLength={8}
                      value={
                        form.confirmation_mot_de_passe
                      }
                      onChange={(event) =>
                        modifierChamp(
                          "confirmation_mot_de_passe",
                          event.target.value
                        )
                      }
                      placeholder="Retaper le mot de passe"
                    />

                  </div>

                </div>

              </div>

              {/* ==================================================
                  5 — ÉGLISE
                  ================================================== */}

              <div className="form-section">

                <h4>
                  5. Église de rattachement
                </h4>

                <div className="rattachement-card">

                  <div>

                    <span>
                      Église
                    </span>

                    <strong>
                      {egliseNom}
                    </strong>

                  </div>

                  <span className="scope-badge">
                    COMPTE ACTUEL
                  </span>

                </div>

                <p className="form-help">
                  L'église est automatiquement
                  déterminée par le compte connecté.
                  Elle ne peut pas être modifiée depuis
                  cet écran.
                </p>

              </div>

              {/* ==================================================
                  6 — RÔLE
                  ================================================== */}

              <div className="form-section">

                <h4>
                  6. Rôle *
                </h4>

                <div className="form-champ">

                  <label htmlFor="role">
                    Sélectionner le rôle
                  </label>

                  <select
                    id="role"
                    required
                    value={form.role}
                    onChange={(event) =>
                      modifierChamp(
                        "role",
                        event.target.value
                      )
                    }
                  >

                    <option value="">
                      — Sélectionner un rôle —
                    </option>

                    {ROLES_DISPONIBLES.map(
                      (role) => (
                        <option
                          key={role.value}
                          value={role.value}
                        >
                          {role.label} —{" "}
                          {role.value}
                        </option>
                      )
                    )}

                  </select>

                </div>

                {form.role && (
                  <div className="rattachement-card">

                    <div>

                      <span>
                        Rôle sélectionné
                      </span>

                      <strong>
                        {obtenirRoleLabel(
                          form.role
                        )}
                      </strong>

                    </div>

                    <span className="scope-badge">
                      {form.role}
                    </span>

                  </div>
                )}

                <p className="form-help">
                  Le rôle est choisi par le créateur
                  du compte. Le serveur vérifie ensuite
                  que ce rôle peut être attribué par
                  votre compte.
                </p>

              </div>

              {/* ==================================================
                  7 — PERMISSIONS
                  ================================================== */}

              <div className="form-section">

                <h4>
                  7. Permissions
                </h4>

                <p className="sous-titre">
                  Choisissez les espaces que ce compte
                  pourra gérer dans{" "}
                  <strong>
                    {egliseNom}
                  </strong>.
                </p>

                <div className="permissions-admin-grid">

                  {permissionsDisponibles.length ? (
                    permissionsDisponibles.map(
                      (permission) => (
                        <label
                          key={
                            permission.code
                          }
                          className={
                            "permission-card " +
                            (!permission.id
                              ? "disabled"
                              : "")
                          }
                        >

                          <input
                            type="checkbox"
                            disabled={
                              !permission.id
                            }
                            checked={
                              permission.id
                                ? permissionsSelectionnees.has(
                                    permission.id
                                  )
                                : false
                            }
                            onChange={() =>
                              basculerPermission(
                                permission
                              )
                            }
                          />

                          <span>

                            <b>
                              {permission.label ||
                                permission.libelle ||
                                permission.code}
                            </b>

                            <small>
                              {permission.description ||
                                ""}
                            </small>

                            {!permission.id && (
                              <em>
                                Permission non
                                configurée côté
                                serveur
                              </em>
                            )}

                          </span>

                        </label>
                      )
                    )
                  ) : (
                    <div className="empty-state">
                      Aucune permission disponible.
                      Vérifiez la configuration de
                      /permissions-eglise/.
                    </div>
                  )}

                </div>

              </div>

              {/* ==================================================
                  RÉSUMÉ
                  ================================================== */}

              <div className="creation-resume">

                <h4>
                  Résumé du compte
                </h4>

                <div className="resume-grid">

                  <div>

                    <span>
                      Utilisateur
                    </span>

                    <strong>
                      {form.prenom.trim() ||
                        "Prénom"}{" "}
                      {form.nom.trim() ||
                        "Nom"}
                    </strong>

                  </div>

                  <div>

                    <span>
                      Église
                    </span>

                    <strong>
                      {egliseNom}
                    </strong>

                  </div>

                  <div>

                    <span>
                      Rôle
                    </span>

                    <strong>
                      {form.role
                        ? obtenirRoleLabel(
                            form.role
                          )
                        : "Non sélectionné"}
                    </strong>

                  </div>

                  <div>

                    <span>
                      Permissions
                    </span>

                    <strong>
                      {
                        form.permissions
                          .length
                      }
                    </strong>

                  </div>

                </div>

              </div>

              {/* ==================================================
                  ACTIONS
                  ================================================== */}

              <div className="modal-actions">

                <button
                  type="submit"
                  className="btn"
                  disabled={
                    creationEnCours
                  }
                >
                  {creationEnCours
                    ? "Création du compte…"
                    : "Créer l'utilisateur"}
                </button>

                <button
                  type="button"
                  className="btn btn-secondaire"
                  onClick={
                    fermerModal
                  }
                  disabled={
                    creationEnCours
                  }
                >
                  Annuler
                </button>

              </div>

            </form>

          </div>

        </div>
      )}

    </div>
  );
}
