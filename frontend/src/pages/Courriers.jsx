
import { useCallback, useEffect, useState } from "react";
import client from "../api/client";
import { useAuth } from "../context/AuthContext";

const liste = (data) =>
  Array.isArray(data) ? data : data?.results || data?.data || [];

const messageErreur = (err, defaut) => {
  const data = err?.response?.data;
  if (data?.detail) return data.detail;
  if (data && typeof data === "object") {
    const messages = Object.entries(data)
      .map(([champ, valeur]) => {
        const texte = Array.isArray(valeur)
          ? valeur.join(", ")
          : typeof valeur === "string"
            ? valeur
            : JSON.stringify(valeur);
        return `${champ} : ${texte}`;
      })
      .join(" | ");
    if (messages) return messages;
  }
  return defaut;
};

const nomComplet = (membre) =>
  [membre?.prenom, membre?.nom].filter(Boolean).join(" ") ||
  membre?.nom_complet ||
  membre?.identifiant ||
  "Membre";

const valeurMembre = (...valeurs) =>
  valeurs.find(
    (valeur) =>
      valeur !== null &&
      valeur !== undefined &&
      String(valeur).trim() !== ""
  ) || "";

export default function Courriers() {
  const { utilisateur, estCoordinateur } = useAuth();
  const estPasteur = utilisateur?.role === "PASTEUR";
  const peutCourrier = estPasteur || estCoordinateur;

  const [courriers, setCourriers] = useState([]);
  const [afficherFormulaire, setAfficherFormulaire] = useState(false);
  const [chargement, setChargement] = useState(true);
  const [erreur, setErreur] = useState("");

  const charger = useCallback(async () => {
    setChargement(true);
    setErreur("");

    try {
      const res = await client.get("/courriers/");
      setCourriers(liste(res.data));
    } catch (err) {
      setErreur(
        messageErreur(err, "Impossible de charger les courriers.")
      );
    } finally {
      setChargement(false);
    }
  }, []);

  useEffect(() => {
    charger();
  }, [charger]);

  const telecharger = async (courrier) => {
    setErreur("");

    try {
      const res = await client.get(
        `/courriers/${courrier.id}/telecharger/`,
        { responseType: "blob" }
      );

      const url = window.URL.createObjectURL(
        new Blob([res.data], { type: "application/pdf" })
      );
      const lien = document.createElement("a");
      lien.href = url;
      lien.download = `${String(
        courrier.numero_reference || `courrier-${courrier.id}`
      ).replace(/\//g, "-")}.pdf`;

      document.body.appendChild(lien);
      lien.click();
      lien.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setErreur(
        messageErreur(err, "Téléchargement du PDF impossible.")
      );
    }
  };

  const marquerRecu = async (courrier) => {
    setErreur("");

    try {
      await client.post(
        `/courriers/${courrier.id}/marquer_recu/`
      );
      await charger();
    } catch (err) {
      setErreur(
        messageErreur(
          err,
          "Vous n'êtes pas autorisé à réceptionner ce courrier."
        )
      );
    }
  };

  const peutReceptionner = (courrier) =>
    estPasteur &&
    !courrier.lu &&
    Boolean(utilisateur?.eglise) &&
    String(courrier.eglise_destinataire) ===
      String(utilisateur.eglise);

  return (
    <div className="page-shell">
      <div className="page-hero">
        <div>
          <span className="eyebrow">COURRIERS EESAG</span>
          <h1>Correspondances officielles</h1>
          <p>
            {estCoordinateur
              ? "Préparez et envoyez les lettres nationales officielles vers les églises, le Bureau national ou un destinataire désigné."
              : "Préparez les recommandations pastorales, consultez les courriers reçus et confirmez leur réception."}
          </p>
        </div>

        {peutCourrier && (
          <button
            type="button"
            className="btn"
            onClick={() => {
              setErreur("");
              setAfficherFormulaire(true);
            }}
          >
            {estCoordinateur
              ? "+ Nouvelle lettre nationale"
              : "+ Nouvelle recommandation"}
          </button>
        )}
      </div>

      {!peutCourrier && (
        <div className="console-error">
          La gestion des courriers est réservée au Coordinateur du système
          et aux pasteurs des églises.
        </div>
      )}

      {erreur && (
        <div className="console-error" role="alert">
          {erreur}
        </div>
      )}

      <div className="carte">
        <div className="section-header">
          <div>
            <span className="eyebrow">BOÎTE OFFICIELLE</span>
            <h3>Courriers envoyés et reçus</h3>
          </div>

          <span className="scope-badge">
            {utilisateur?.eglise_nom ||
              (estCoordinateur ? "Coordination nationale" : "—")}
          </span>
        </div>

        {chargement ? (
          <div className="empty-state">Chargement des courriers…</div>
        ) : (
          <div className="table-responsive">
            <table>
              <thead>
                <tr>
                  <th>Référence</th>
                  <th>Type</th>
                  <th>Objet</th>
                  <th>Destination</th>
                  <th>Date</th>
                  <th>État</th>
                  <th>Actions</th>
                </tr>
              </thead>

              <tbody>
                {courriers.map((c) => (
                  <tr key={c.id}>
                    <td>{c.numero_reference || "—"}</td>
                    <td>
                      {c.type_courrier_libelle ||
                        ({
                          RECOMMANDATION: "Recommandation pastorale",
                          NATIONALE: "Lettre nationale officielle",
                          MISSION: "Mission",
                          NOTE: "Note",
                        }[c.type_courrier] ||
                          c.type_courrier ||
                          "—")}
                    </td>
                    <td>{c.objet || "—"}</td>
                    <td>
                      {c.eglise_destinataire_nom ||
                        c.destinataire_nom ||
                        c.type_destinataire_libelle ||
                        "—"}
                    </td>
                    <td>{c.date_emission || "—"}</td>
                    <td>
                      <span
                        className={`status-chip ${
                          c.lu ? "ok" : "pending"
                        }`}
                      >
                        {c.lu ? "Reçu" : "En attente"}
                      </span>
                    </td>
                    <td>
                      <div className="actions">
                        <button
                          type="button"
                          className="btn btn-petit btn-secondaire"
                          onClick={() => telecharger(c)}
                        >
                          PDF
                        </button>

                        {c.fichier_word && (
                          <a
                            className="btn btn-petit"
                            href={c.fichier_word}
                            target="_blank"
                            rel="noreferrer"
                          >
                            Word
                          </a>
                        )}

                        {peutReceptionner(c) && (
                          <button
                            type="button"
                            className="btn btn-petit"
                            onClick={() => marquerRecu(c)}
                          >
                            Réceptionner
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}

                {!courriers.length && (
                  <tr>
                    <td
                      colSpan={7}
                      style={{
                        textAlign: "center",
                        color: "#64748b",
                        padding: 28,
                      }}
                    >
                      Aucun courrier dans votre périmètre.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {afficherFormulaire && peutCourrier && (
        <FormulaireCourrier
          mode={estCoordinateur ? "NATIONALE" : "RECOMMANDATION"}
          utilisateur={utilisateur}
          onFerme={() => setAfficherFormulaire(false)}
          onCree={async () => {
            setAfficherFormulaire(false);
            await charger();
          }}
        />
      )}
    </div>
  );
}

function FormulaireCourrier({
  mode,
  utilisateur,
  onFerme,
  onCree,
}) {
  const estNational = mode === "NATIONALE";

  const [eglises, setEglises] = useState([]);
  const [chargementEglises, setChargementEglises] = useState(true);
  const [terme, setTerme] = useState("");
  const [membresTrouves, setMembresTrouves] = useState([]);
  const [membreSelectionne, setMembreSelectionne] = useState(null);
  const [preview, setPreview] = useState(null);
  const [erreur, setErreur] = useState("");
  const [busy, setBusy] = useState(false);

  const [form, setForm] = useState({
    type_courrier: estNational ? "NATIONALE" : "RECOMMANDATION",
    type_destinataire: "EGLISE",
    destinataire_nom: "",
    eglise_destinataire: "",
    membre_concerne: "",
    objet: estNational
      ? "Courrier officiel"
      : "Lettre de recommandation",
    contenu: "",
    lieu_emission: "Conakry",
    fichier_word: null,
  });

  const [details, setDetails] = useState({
    motif_depart: "",
    date_bapteme: "",
    lieu_bapteme: "",
    situation_matrimoniale: "",
    fonction_eglise: "",
    stabilite: "",
    fidelite: "",
    soumission: "",
    observations: "",
  });

  const modifier = (champ, valeur) => {
    setForm((ancien) => ({ ...ancien, [champ]: valeur }));
    setPreview(null);
    setErreur("");
  };

  const modifierDetail = (champ, valeur) => {
    setDetails((ancien) => ({ ...ancien, [champ]: valeur }));
    setPreview(null);
    setErreur("");
  };

  useEffect(() => {
    let actif = true;

    client
      .get("/eglises/")
      .then((res) => {
        if (actif) setEglises(liste(res.data));
      })
      .catch((err) => {
        if (actif) {
          setErreur(
            messageErreur(
              err,
              "Impossible de charger la liste des églises."
            )
          );
        }
      })
      .finally(() => {
        if (actif) setChargementEglises(false);
      });

    return () => {
      actif = false;
    };
  }, []);

  useEffect(() => {
    if (estNational) return undefined;

    const recherche = terme.trim();

    if (recherche.length < 2) {
      setMembresTrouves([]);
      return undefined;
    }

    let actif = true;
    const timer = setTimeout(() => {
      client
        .get("/membres/recherche/", {
          params: { q: recherche },
        })
        .then((res) => {
          if (actif) setMembresTrouves(liste(res.data));
        })
        .catch(() => {
          if (actif) setMembresTrouves([]);
        });
    }, 300);

    return () => {
      actif = false;
      clearTimeout(timer);
    };
  }, [terme, estNational]);

  const selectionnerMembre = (event) => {
    const id = event.target.value;
    const membre = membresTrouves.find(
      (element) => String(element.id) === String(id)
    );

    setMembreSelectionne(membre || null);
    setPreview(null);
    setErreur("");

    setForm((ancien) => ({
      ...ancien,
      membre_concerne: id,
    }));

    if (!membre) return;

    setTerme(nomComplet(membre));

    setDetails((ancien) => ({
      ...ancien,
      date_bapteme: valeurMembre(
        membre.date_bapteme_eau,
        membre.date_bapteme
      ),
      lieu_bapteme: valeurMembre(
        membre.lieu_bapteme,
        membre.lieu_bapteme_eau
      ),
      situation_matrimoniale: valeurMembre(
        membre.situation_matrimoniale,
        membre.situation_familiale
      ),
      fonction_eglise: valeurMembre(
        membre.fonction_eglise,
        membre.fonction,
        membre.role_eglise
      ),
    }));
  };

  const egliseOrigine = valeurMembre(
    membreSelectionne?.eglise_nom,
    membreSelectionne?.eglise?.nom,
    membreSelectionne?.nom_eglise,
    utilisateur?.eglise_nom,
    utilisateur?.eglise?.nom
  );

  const telephoneMembre = valeurMembre(
    membreSelectionne?.telephone,
    membreSelectionne?.numero_telephone
  );

  const emailMembre = valeurMembre(membreSelectionne?.email);

  const construireContenuRecommandation = () => {
    const engagement = [
      ["Stabilité spirituelle", details.stabilite],
      ["Fidélité", details.fidelite],
      ["Soumission", details.soumission],
    ]
      .filter(([, valeur]) => valeur)
      .map(([titre, valeur]) => `${titre} : ${valeur}`)
      .join("\n");

    return [
      "LETTRE DE RECOMMANDATION",
      "",
      "À l'attention du pasteur et des responsables de l'église destinataire,",
      "",
      "Que la grâce et la paix de Dieu le Père et de notre Seigneur Jésus-Christ soient avec vous.",
      "",
      `Nous, responsables de l'église ${egliseOrigine || "d'origine"}, recommandons à votre communion fraternelle le membre suivant :`,
      "",
      `Nom complet : ${nomComplet(membreSelectionne)}`,
      `Identifiant EESAG : ${membreSelectionne?.identifiant || ""}`,
      `Téléphone : ${telephoneMembre || "Non renseigné"}`,
      `Adresse e-mail : ${emailMembre || "Non renseignée"}`,
      `Église d'origine : ${egliseOrigine || "Non renseignée"}`,
      `Fonction dans l'église : ${details.fonction_eglise || "Non renseignée"}`,
      `Baptême : ${details.date_bapteme || "Non renseigné"}`,
      `Lieu du baptême : ${details.lieu_bapteme || "Non renseigné"}`,
      `Situation matrimoniale : ${details.situation_matrimoniale || "Non renseignée"}`,
      "",
      "MOTIF DU DÉPLACEMENT",
      details.motif_depart || "À compléter par le pasteur.",
      "",
      "ENGAGEMENT ET APPRÉCIATION PASTORALE",
      engagement || "Appréciation pastorale à compléter.",
      "",
      "OBSERVATIONS COMPLÉMENTAIRES",
      details.observations || "Aucune observation complémentaire.",
      "",
      "Nous vous prions de bien vouloir accueillir ce membre dans un esprit de communion fraternelle.",
      "",
      "Fait pour servir et valoir ce que de droit.",
      "",
      `Pasteur de l'église d'origine : ${utilisateur?.prenom || ""} ${utilisateur?.nom || ""}`.trim(),
    ].join("\n");
  };

  const contenuFinal = () =>
    estNational
      ? form.contenu.trim()
      : construireContenuRecommandation();

  const creerFormData = () => {
    const fd = new FormData();

    fd.append("type_courrier", form.type_courrier);
    fd.append("objet", form.objet.trim());
    fd.append("contenu", contenuFinal());

    if (estNational) {
      fd.append("type_destinataire", form.type_destinataire);
      fd.append("lieu_emission", form.lieu_emission.trim() || "Conakry");

      if (form.type_destinataire === "EGLISE") {
        fd.append("eglise_destinataire", form.eglise_destinataire);
      } else {
        fd.append("destinataire_nom", form.type_destinataire === "BUREAU_NATIONAL"
          ? form.destinataire_nom.trim() || "Bureau national"
          : form.destinataire_nom.trim());
      }
    } else {
      fd.append("eglise_destinataire", form.eglise_destinataire);
      fd.append("membre_concerne", form.membre_concerne);

      if (form.fichier_word) {
        fd.append("fichier_word", form.fichier_word);
      }
    }

    return fd;
  };

  const validerFormulaire = () => {
    if (!form.objet.trim()) {
      return "L'objet du courrier est obligatoire.";
    }

    if (estNational) {
      if (!contenuFinal()) {
        return "Le contenu de la lettre officielle est obligatoire.";
      }

      if (
        form.type_destinataire === "EGLISE" &&
        !form.eglise_destinataire
      ) {
        return "Sélectionne l'église destinataire.";
      }

      if (
        form.type_destinataire === "AUTRE" &&
        !form.destinataire_nom.trim()
      ) {
        return "Indique le nom de la personne ou de la structure destinataire.";
      }

      return "";
    }

    if (!form.membre_concerne || !membreSelectionne) {
      return "Recherche et sélectionne un membre actif de ton église.";
    }

    if (!form.eglise_destinataire) {
      return "Sélectionne l'église de destination.";
    }

    if (!details.motif_depart.trim()) {
      return "Le motif du déplacement est obligatoire.";
    }

    return "";
  };

  const apercu = async () => {
    setErreur("");
    setPreview(null);

    const validation = validerFormulaire();
    if (validation) {
      setErreur(validation);
      return;
    }

    setBusy(true);

    try {
      const { data } = await client.post(
        "/courriers/apercu/",
        creerFormData()
      );
      setPreview(data);
    } catch (err) {
      setErreur(
        messageErreur(err, "Impossible de générer l'aperçu.")
      );
    } finally {
      setBusy(false);
    }
  };

  const envoyer = async () => {
    if (!preview) {
      setErreur("Génère d'abord l'aperçu du courrier.");
      return;
    }

    const validation = validerFormulaire();
    if (validation) {
      setErreur(validation);
      return;
    }

    setErreur("");
    setBusy(true);

    try {
      await client.post("/courriers/", creerFormData());
      await onCree();
    } catch (err) {
      setErreur(
        messageErreur(err, "L'envoi du courrier a échoué.")
      );
    } finally {
      setBusy(false);
    }
  };

  const titre = estNational
    ? "Nouvelle lettre nationale officielle"
    : "Nouvelle lettre de recommandation";

  const destinationSelectionnee = eglises.find(
    (eglise) =>
      String(eglise.id) === String(form.eglise_destinataire)
  );

  return (
    <div
      className="modale-fond"
      onClick={() => !busy && onFerme()}
    >
      <div
        className="modale courrier-editor"
        role="dialog"
        aria-modal="true"
        aria-labelledby="titre-formulaire-courrier"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="modal-header">
          <div>
            <span className="eyebrow">
              {estNational
                ? "EESAG · COORDINATION NATIONALE"
                : "EESAG · PASTEUR"}
            </span>
            <h3 id="titre-formulaire-courrier">{titre}</h3>
          </div>

          <button
            type="button"
            className="modal-close"
            onClick={onFerme}
            disabled={busy}
            aria-label="Fermer"
          >
            ×
          </button>
        </div>

        <div className="editor-grid">
          <div>
            {estNational ? (
              <>
                <div className="form-champ">
                  <label htmlFor="type-destinataire">
                    Type de destinataire *
                  </label>
                  <select
                    id="type-destinataire"
                    value={form.type_destinataire}
                    onChange={(event) => {
                      const type = event.target.value;
                      setForm((ancien) => ({
                        ...ancien,
                        type_destinataire: type,
                        eglise_destinataire: "",
                        destinataire_nom:
                          type === "BUREAU_NATIONAL"
                            ? "Bureau national"
                            : "",
                      }));
                      setPreview(null);
                      setErreur("");
                    }}
                  >
                    <option value="EGLISE">Église active</option>
                    <option value="BUREAU_NATIONAL">Bureau national</option>
                    <option value="AUTRE">Autre destinataire</option>
                  </select>
                </div>

                {form.type_destinataire === "EGLISE" && (
                  <div className="form-champ">
                    <label htmlFor="eglise-nationale">
                      Église destinataire *
                    </label>
                    <select
                      id="eglise-nationale"
                      required
                      value={form.eglise_destinataire}
                      onChange={(event) =>
                        modifier(
                          "eglise_destinataire",
                          event.target.value
                        )
                      }
                      disabled={chargementEglises}
                    >
                      <option value="">
                        {chargementEglises
                          ? "Chargement des églises…"
                          : "— Choisir une église —"}
                      </option>
                      {eglises.map((eglise) => (
                        <option key={eglise.id} value={eglise.id}>
                          {eglise.nom}
                          {eglise.code ? ` (${eglise.code})` : ""}
                        </option>
                      ))}
                    </select>
                    <small className="helper-text">
                      Le serveur vérifie que la plateforme de l'église est active.
                    </small>
                  </div>
                )}

                {form.type_destinataire !== "EGLISE" && (
                  <div className="form-champ">
                    <label htmlFor="destinataire-nom">
                      {form.type_destinataire === "BUREAU_NATIONAL"
                        ? "Nom du destinataire"
                        : "Nom de la personne ou de la structure *"}
                    </label>
                    <input
                      id="destinataire-nom"
                      value={form.destinataire_nom}
                      onChange={(event) =>
                        modifier("destinataire_nom", event.target.value)
                      }
                      placeholder={
                        form.type_destinataire === "BUREAU_NATIONAL"
                          ? "Bureau national"
                          : "Nom du destinataire"
                      }
                    />
                  </div>
                )}

                <div className="form-champ">
                  <label htmlFor="lieu-emission">
                    Lieu d'émission
                  </label>
                  <input
                    id="lieu-emission"
                    value={form.lieu_emission}
                    onChange={(event) =>
                      modifier("lieu_emission", event.target.value)
                    }
                    placeholder="Ex. : Conakry"
                  />
                </div>

                <div className="form-champ">
                  <label htmlFor="objet-national">
                    Objet de la lettre *
                  </label>
                  <input
                    id="objet-national"
                    required
                    value={form.objet}
                    onChange={(event) =>
                      modifier("objet", event.target.value)
                    }
                    placeholder="Objet officiel du courrier"
                  />
                </div>

                <div className="form-champ">
                  <label htmlFor="contenu-national">
                    Contenu de la lettre officielle *
                  </label>
                  <textarea
                    id="contenu-national"
                    rows={12}
                    required
                    value={form.contenu}
                    onChange={(event) =>
                      modifier("contenu", event.target.value)
                    }
                    placeholder={"Madame, Monsieur,\n\nNous avons l'honneur de vous écrire au sujet de…\n\nVeuillez agréer nos salutations distinguées."}
                  />
                </div>

                <p className="helper-text">
                  Cette lettre est distincte d'une recommandation pastorale.
                  Rédige le texte officiel qui sera prévisualisé avant l'envoi.
                </p>
              </>
            ) : (
              <>
                <div className="form-champ">
                  <label htmlFor="recherche-membre">
                    Rechercher un membre *
                  </label>
                  <input
                    id="recherche-membre"
                    value={terme}
                    onChange={(event) => {
                      setTerme(event.target.value);
                      setMembreSelectionne(null);
                      setForm((ancien) => ({
                        ...ancien,
                        membre_concerne: "",
                      }));
                      setPreview(null);
                      setErreur("");
                    }}
                    placeholder="Nom, prénom ou identifiant…"
                    autoComplete="off"
                  />

                  {membresTrouves.length > 0 && (
                    <select
                      aria-label="Choisir le membre"
                      size={Math.min(membresTrouves.length, 5)}
                      value={form.membre_concerne}
                      onChange={selectionnerMembre}
                    >
                      <option value="">
                        — Sélectionner le membre —
                      </option>
                      {membresTrouves.map((membre) => (
                        <option key={membre.id} value={membre.id}>
                          {nomComplet(membre)} — {membre.identifiant || membre.id}
                        </option>
                      ))}
                    </select>
                  )}
                </div>

                {membreSelectionne && (
                  <section className="carte mb-3">
                    <div className="section-header">
                      <div>
                        <span className="eyebrow">FICHE DU MEMBRE</span>
                        <h4>{nomComplet(membreSelectionne)}</h4>
                      </div>
                      <span className="status-chip ok">Sélectionné</span>
                    </div>
                    <div className="p-3">
                      <p>
                        <strong>Identifiant :</strong>{" "}
                        {membreSelectionne.identifiant || "—"}
                      </p>
                      <p>
                        <strong>Téléphone :</strong> {telephoneMembre || "—"}
                      </p>
                      <p>
                        <strong>E-mail :</strong> {emailMembre || "—"}
                      </p>
                      <p>
                        <strong>Église d'origine :</strong> {egliseOrigine || "—"}
                      </p>
                    </div>
                  </section>
                )}

                <div className="form-champ">
                  <label htmlFor="eglise-destination">
                    Église de destination *
                  </label>
                  <select
                    id="eglise-destination"
                    required
                    value={form.eglise_destinataire}
                    onChange={(event) =>
                      modifier("eglise_destinataire", event.target.value)
                    }
                    disabled={chargementEglises}
                  >
                    <option value="">
                      {chargementEglises
                        ? "Chargement des églises…"
                        : "— Choisir l'église —"}
                    </option>
                    {eglises
                      .filter(
                        (eglise) =>
                          String(eglise.id) !==
                          String(
                            membreSelectionne?.eglise ??
                              membreSelectionne?.eglise_id ??
                              utilisateur?.eglise ??
                              utilisateur?.eglise_id ??
                              ""
                          )
                      )
                      .map((eglise) => (
                        <option key={eglise.id} value={eglise.id}>
                          {eglise.nom} {eglise.code ? `(${eglise.code})` : ""}
                        </option>
                      ))}
                  </select>
                </div>

                <div className="form-champ">
                  <label htmlFor="objet-lettre">
                    Objet de la lettre *
                  </label>
                  <input
                    id="objet-lettre"
                    required
                    value={form.objet}
                    onChange={(event) =>
                      modifier("objet", event.target.value)
                    }
                  />
                </div>

                <div className="form-champ">
                  <label htmlFor="motif-depart">
                    Motif du déplacement *
                  </label>
                  <textarea
                    id="motif-depart"
                    rows={3}
                    required
                    value={details.motif_depart}
                    onChange={(event) =>
                      modifierDetail("motif_depart", event.target.value)
                    }
                    placeholder="Mutation professionnelle, déménagement, mariage, études…"
                  />
                </div>

                <h4 className="mt-4">Informations complémentaires</h4>

                <div className="form-champ">
                  <label htmlFor="date-bapteme">Date du baptême d'eau</label>
                  <input
                    id="date-bapteme"
                    type="date"
                    value={details.date_bapteme}
                    onChange={(event) =>
                      modifierDetail("date_bapteme", event.target.value)
                    }
                  />
                </div>

                <div className="form-champ">
                  <label htmlFor="lieu-bapteme">Lieu du baptême</label>
                  <input
                    id="lieu-bapteme"
                    value={details.lieu_bapteme}
                    onChange={(event) =>
                      modifierDetail("lieu_bapteme", event.target.value)
                    }
                    placeholder="Lieu du baptême, si connu"
                  />
                </div>

                <div className="form-champ">
                  <label htmlFor="situation-matrimoniale">
                    Situation matrimoniale
                  </label>
                  <select
                    id="situation-matrimoniale"
                    value={details.situation_matrimoniale}
                    onChange={(event) =>
                      modifierDetail(
                        "situation_matrimoniale",
                        event.target.value
                      )
                    }
                  >
                    <option value="">— Non renseignée —</option>
                    <option value="Célibataire">Célibataire</option>
                    <option value="Marié(e)">Marié(e)</option>
                    <option value="Veuf / Veuve">Veuf / Veuve</option>
                    <option value="Divorcé(e)">Divorcé(e)</option>
                    <option value="Autre">Autre</option>
                  </select>
                </div>

                <div className="form-champ">
                  <label htmlFor="fonction-eglise">
                    Fonction dans l'église
                  </label>
                  <input
                    id="fonction-eglise"
                    value={details.fonction_eglise}
                    onChange={(event) =>
                      modifierDetail("fonction_eglise", event.target.value)
                    }
                    placeholder="Membre, moniteur, responsable…"
                  />
                </div>

                <h4 className="mt-4">Appréciation pastorale</h4>
                <p className="helper-text">
                  À compléter selon l'engagement réel du membre.
                </p>

                {[
                  ["stabilite", "Stabilité spirituelle"],
                  ["fidelite", "Fidélité"],
                  ["soumission", "Soumission et respect de l'encadrement"],
                ].map(([champ, titre]) => (
                  <div className="form-champ" key={champ}>
                    <label htmlFor={`engagement-${champ}`}>{titre}</label>
                    <select
                      id={`engagement-${champ}`}
                      value={details[champ]}
                      onChange={(event) =>
                        modifierDetail(champ, event.target.value)
                      }
                    >
                      <option value="">— À évaluer —</option>
                      <option value="Satisfaisant">Satisfaisant</option>
                      <option value="À améliorer">À améliorer</option>
                      <option value="Non évalué">Non évalué</option>
                    </select>
                  </div>
                ))}

                <div className="form-champ">
                  <label htmlFor="observations-pastorales">
                    Observations complémentaires
                  </label>
                  <textarea
                    id="observations-pastorales"
                    rows={4}
                    value={details.observations}
                    onChange={(event) =>
                      modifierDetail("observations", event.target.value)
                    }
                    placeholder="Responsabilités, engagement, appréciation pastorale…"
                  />
                </div>

                <div className="form-champ">
                  <label htmlFor="fichier-word">
                    Modèle Word signé et cacheté (facultatif)
                  </label>
                  <input
                    id="fichier-word"
                    type="file"
                    accept=".doc,.docx"
                    onChange={(event) =>
                      modifier("fichier_word", event.target.files?.[0] || null)
                    }
                  />
                  <small className="helper-text">
                    {form.fichier_word?.name ||
                      "Aucun document Word sélectionné"}
                  </small>
                </div>
              </>
            )}

            {erreur && (
              <div className="console-error" role="alert">
                {erreur}
              </div>
            )}

            <div className="modal-actions">
              <button
                type="button"
                className="btn btn-secondaire"
                onClick={onFerme}
                disabled={busy}
              >
                Annuler
              </button>
              <button
                type="button"
                className="btn"
                onClick={apercu}
                disabled={busy}
              >
                {busy ? "Préparation…" : "Générer l'aperçu"}
              </button>
            </div>
          </div>

          <div className="preview-pane">
            <span className="eyebrow">APERÇU DU COURRIER</span>

            {!preview ? (
              <div className="preview-empty">
                <span>▣</span>
                <p>
                  {estNational
                    ? "Choisis le destinataire, renseigne l'objet et le contenu, puis génère l'aperçu."
                    : "Sélectionne un membre, complète les informations nécessaires, puis génère l'aperçu."}
                </p>
              </div>
            ) : (
              <>
                <div className="preview-paper">
                  <div className="preview-brand">EESAG</div>
                  <h4>{preview.objet || form.objet}</h4>

                  {estNational ? (
                    <>
                      <p>
                        <strong>Type :</strong> Lettre nationale officielle
                      </p>
                      <p>
                        <strong>Destinataire :</strong>{" "}
                        {preview.destinataire_nom ||
                          preview.eglise_destinataire ||
                          destinationSelectionnee?.nom ||
                          "—"}
                      </p>
                      <p>
                        <strong>Lieu d'émission :</strong>{" "}
                        {preview.lieu_emission || form.lieu_emission || "—"}
                      </p>
                    </>
                  ) : (
                    <>
                      <p>
                        <strong>Membre :</strong>{" "}
                        {preview.membre_nom || nomComplet(membreSelectionne)}
                      </p>
                      <p>
                        <strong>Identifiant :</strong>{" "}
                        {preview.membre_identifiant ||
                          membreSelectionne?.identifiant ||
                          "—"}
                      </p>
                      <p>
                        <strong>Église d'origine :</strong>{" "}
                        {preview.eglise_origine || egliseOrigine || "—"}
                      </p>
                      <p>
                        <strong>Église destinataire :</strong>{" "}
                        {preview.eglise_destinataire ||
                          destinationSelectionnee?.nom ||
                          "—"}
                      </p>
                    </>
                  )}

                  <hr />

                  <div
                    className="preview-text"
                    style={{
                      whiteSpace: "pre-wrap",
                      overflowWrap: "anywhere",
                    }}
                  >
                    {preview.contenu || contenuFinal()}
                  </div>

                  {preview.message && (
                    <p className="helper-text">{preview.message}</p>
                  )}
                </div>

                <button
                  type="button"
                  className="btn btn-secondaire w-100 mb-2"
                  onClick={apercu}
                  disabled={busy}
                >
                  Actualiser l'aperçu
                </button>

                <button
                  type="button"
                  className="btn w-100"
                  onClick={envoyer}
                  disabled={busy}
                >
                  {busy
                    ? "Envoi en cours…"
                    : "Valider et envoyer le courrier"}
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
