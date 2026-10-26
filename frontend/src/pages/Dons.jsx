import { useState } from "react";

export default function Dons() {
  const [montant, setMontant] = useState("");
  const [operateur, setOperateur] = useState("orange");
  const [telephone, setTelephone] = useState("");
  const [confirmation, setConfirmation] = useState(null);
  const [erreur, setErreur] = useState("");

  const validerDon = (e) => {
    e.preventDefault();
    setErreur("");
    setConfirmation(null);

    const montantNumerique = Number(montant);
    const numeroNettoye = telephone.trim();

    if (!Number.isFinite(montantNumerique) || montantNumerique < 500) {
      setErreur("Veuillez saisir un montant d'au moins 500 FCFA.");
      return;
    }

    // Accepte un numéro guinéen local ou international.
    const numeroValide = /^(?:(?:\+224|00224)\s*)?(?:\d[\s.-]*){9}$/.test(
      numeroNettoye
    );

    if (!numeroValide) {
      setErreur(
        "Veuillez saisir un numéro de téléphone valide, au format local ou international (+224)."
      );
      return;
    }

    setConfirmation({
      montant: montantNumerique,
      operateur:
        operateur === "orange" ? "Orange Money" : "MTN Mobile Money",
      telephone: numeroNettoye,
      date: new Date().toLocaleString("fr-FR"),
    });
  };

  const nouvelleDemande = () => {
    setMontant("");
    setOperateur("orange");
    setTelephone("");
    setConfirmation(null);
    setErreur("");
  };

  return (
    <div className="page-standard">
      <div className="page-hero">
        <div>
          <span className="eyebrow">SOUTENIR L'ŒUVRE</span>
          <h1>❤ Faire un don</h1>
          <p>
            Votre soutien contribue au développement des activités
            et des projets de l'EESAG.
          </p>
        </div>
      </div>

      <section className="carte donation-form">
        {!confirmation ? (
          <form onSubmit={validerDon}>
            <div className="form-champ">
              <label htmlFor="montant-don">Montant du don</label>
              <div className="money-input">
                <input
                  id="montant-don"
                  type="number"
                  min="500"
                  step="500"
                  required
                  value={montant}
                  onChange={(e) => setMontant(e.target.value)}
                  placeholder="Ex. 50000"
                />
                <span>FCFA</span>
              </div>
            </div>

            <div className="form-champ">
              <label htmlFor="operateur-don">Opérateur Mobile Money</label>
              <select
                id="operateur-don"
                value={operateur}
                onChange={(e) => setOperateur(e.target.value)}
                required
              >
                <option value="orange">Orange Money</option>
                <option value="mtn">MTN Mobile Money</option>
              </select>
            </div>

            <div className="form-champ">
              <label htmlFor="telephone-don">
                Votre numéro de téléphone Mobile Money
              </label>
              <input
                id="telephone-don"
                type="tel"
                autoComplete="tel"
                inputMode="tel"
                required
                value={telephone}
                onChange={(e) => setTelephone(e.target.value)}
                placeholder="Ex. 622 12 34 56 ou +224 622 12 34 56"
              />
              <small>
                Saisissez le numéro associé au compte que vous utiliserez
                pour effectuer le transfert.
              </small>
            </div>

            {erreur && (
              <p className="status-error" role="alert">
                {erreur}
              </p>
            )}

            <button type="submit" className="btn btn-primary">
              Valider le don
            </button>

            <p className="donation-note">
              Cette étape confirme votre demande. Elle ne déclenche pas
              automatiquement un transfert et ne confirme pas le paiement.
            </p>
          </form>
        ) : (
          <div className="donation-confirmation" role="status">
            <h2>✓ Demande de don confirmée</h2>
            <p>Vérifiez les informations de votre demande :</p>

            <div className="donation-details">
              <p>
                <strong>Montant :</strong>{" "}
                {confirmation.montant.toLocaleString("fr-FR")} FCFA
              </p>
              <p>
                <strong>Opérateur :</strong> {confirmation.operateur}
              </p>
              <p>
                <strong>Votre numéro :</strong> {confirmation.telephone}
              </p>
              <p>
                <strong>Date de la demande :</strong> {confirmation.date}
              </p>
            </div>

            <p className="donation-note">
              Votre demande est confirmée dans cette page, mais le transfert
              n'a pas été vérifié. Veuillez effectuer le paiement par le
              service de l'opérateur choisi, puis suivre la procédure de
              vérification prévue par l'EESAG.
            </p>

            <button
              type="button"
              className="btn btn-primary"
              onClick={nouvelleDemande}
            >
              Nouvelle demande de don
            </button>
          </div>
        )}
      </section>
    </div>
  );
}
