"""
Génération des courriers officiels EESAG au format PDF A4.
Prend en charge les lettres de mission, les recommandations
pastorales, les notes de service et les lettres nationales.
"""
import io
import re
from xml.sax.saxutils import escape

from django.core.files.base import ContentFile
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

NOM_ORGANISATION = "PLATEFORME NATIONALE DE GESTION DES ÉGLISES"
SLOGAN_ORGANISATION = "Bureau National de Coordination"


def _texte_securise(valeur):
    """Échappe les caractères interprétés comme balises par ReportLab."""
    return escape(str(valeur or ""))


def _styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="EnteteEESAG",
        parent=styles["Heading1"],
        alignment=TA_CENTER,
        fontSize=14,
        leading=18,
        spaceAfter=4,
    ))

    styles.add(ParagraphStyle(
        name="SousEnteteEESAG",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=10,
        textColor=colors.HexColor("#444444"),
        spaceAfter=16,
    ))

    styles.add(ParagraphStyle(
        name="ReferenceEESAG",
        parent=styles["Normal"],
        alignment=TA_RIGHT,
        fontSize=9,
        leading=14,
        spaceAfter=18,
    ))

    styles.add(ParagraphStyle(
        name="TitreCourrierEESAG",
        parent=styles["Heading2"],
        alignment=TA_CENTER,
        fontSize=13,
        leading=17,
        spaceBefore=10,
        spaceAfter=20,
        textColor=colors.HexColor("#17324d"),
    ))

    styles.add(ParagraphStyle(
        name="CorpsCourrierEESAG",
        parent=styles["Normal"],
        alignment=TA_JUSTIFY,
        fontSize=10.5,
        leading=16,
        spaceAfter=10,
    ))

    styles.add(ParagraphStyle(
        name="SignatureEESAG",
        parent=styles["Normal"],
        alignment=TA_RIGHT,
        fontSize=10,
        leading=15,
        spaceBefore=28,
    ))

    styles.add(ParagraphStyle(
        name="PetitEESAG",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
    ))

    return styles


def _nom_complet(utilisateur):
    if not utilisateur:
        return "Non renseigné"
    return " ".join(
        str(part).strip()
        for part in (
            getattr(utilisateur, "prenom", ""),
            getattr(utilisateur, "nom", ""),
        )
        if part
    ) or getattr(utilisateur, "identifiant", "Non renseigné")


def _destination(courrier):
    """Construit une désignation lisible, y compris sans église liée."""
    eglise = getattr(courrier, "eglise_destinataire", None)

    if eglise:
        localisation = (
            getattr(eglise, "commune", None)
            or getattr(eglise, "district", None)
            or getattr(eglise, "prefecture", None)
        )
        localisation = getattr(localisation, "nom", "") if localisation else ""
        resultat = f"Église « {eglise.nom} »"
        if localisation:
            resultat += f" — {localisation}"
        return resultat

    nom = getattr(courrier, "destinataire_nom", "")
    type_destinataire = getattr(courrier, "type_destinataire", "")

    if nom:
        return nom

    if type_destinataire == "BUREAU_NATIONAL":
        return "Bureau national"

    if type_destinataire == "AUTRE":
        return "Destinataire indiqué par l'expéditeur"

    return "Destinataire non précisé"


def generer_pdf_courrier(courrier) -> ContentFile:
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=2.0 * cm,
        bottomMargin=2.0 * cm,
        leftMargin=2.3 * cm,
        rightMargin=2.3 * cm,
        title=f"Courrier {courrier.numero_reference}",
        author=NOM_ORGANISATION,
    )

    styles = _styles()
    elements = []

    # En-tête institutionnel
    elements.append(Paragraph(
        _texte_securise(NOM_ORGANISATION),
        styles["EnteteEESAG"],
    ))
    elements.append(Paragraph(
        _texte_securise(SLOGAN_ORGANISATION),
        styles["SousEnteteEESAG"],
    ))

    largeur = A4[0] - doc.leftMargin - doc.rightMargin
    ligne = Table([[""]], colWidths=[largeur], rowHeights=[0.04 * cm])
    ligne.setStyle(TableStyle([
        (
            "LINEBELOW",
            (0, 0),
            (-1, -1),
            1.2,
            colors.HexColor("#1a3c5e"),
        ),
    ]))
    elements.append(ligne)
    elements.append(Spacer(1, 14))

    # Référence et date d'émission
    date_emission = getattr(courrier, "date_emission", None)
    date_formatee = (
        date_emission.strftime("%d/%m/%Y")
        if date_emission
        else "Non renseignée"
    )

    lieu = _texte_securise(getattr(courrier, "lieu_emission", "Conakry"))
    reference = _texte_securise(
        getattr(courrier, "numero_reference", "")
    )

    elements.append(Paragraph(
        f"{lieu}, le {date_formatee}<br/>"
        f"<b>Référence :</b> {reference}",
        styles["ReferenceEESAG"],
    ))

    # Type de courrier
    titres = {
        "MISSION": "LETTRE DE MISSION",
        "RECOMMANDATION": "LETTRE DE RECOMMANDATION PASTORALE",
        "NOTE": "NOTE DE SERVICE",
        "NATIONALE": "LETTRE NATIONALE OFFICIELLE",
    }
    titre = titres.get(courrier.type_courrier, "COURRIER OFFICIEL")

    elements.append(Paragraph(
        _texte_securise(titre),
        styles["TitreCourrierEESAG"],
    ))

    # Destinataire : église, Bureau national ou autre personne/structure
    elements.append(Paragraph(
        f"<b>À l'attention de :</b> {_texte_securise(_destination(courrier))}",
        styles["CorpsCourrierEESAG"],
    ))

    # Informations du membre concerné, principalement pour la recommandation
    membre = getattr(courrier, "membre_concerne", None)

    if membre:
        identity_rows = [
            ["Nom complet", _nom_complet(membre)],
            ["Identifiant", getattr(membre, "identifiant", "") or "—"],
            ["Téléphone", getattr(membre, "telephone", "") or "—"],
        ]

        try:
            fonction = membre.get_fonction_eglise_display()
        except (AttributeError, TypeError):
            fonction = ""

        identity_rows.append(["Fonction", fonction or "Membre"])

        departement = getattr(membre, "departement", None)
        if departement:
            identity_rows.append([
                "Département",
                getattr(departement, "nom", ""),
            ])

        role_eglise = getattr(membre, "role_eglise", None)
        if role_eglise:
            identity_rows.append([
                "Rôle dans l'église",
                getattr(role_eglise, "nom", ""),
            ])

        # Échapper les valeurs avant de les transformer en Paragraphs.
        identity_data = [
            [
                Paragraph(
                    f"<b>{_texte_securise(libelle)}</b>",
                    styles["PetitEESAG"],
                ),
                Paragraph(
                    _texte_securise(valeur),
                    styles["PetitEESAG"],
                ),
            ]
            for libelle, valeur in identity_rows
        ]

        table = Table(
            identity_data,
            colWidths=[4.0 * cm, largeur - 4.0 * cm],
            hAlign="LEFT",
            repeatRows=0,
        )
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eef3f7")),
            ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#17324d")),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#cad5df")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 14))

    # Objet
    objet = _texte_securise(getattr(courrier, "objet", "Sans objet"))
    elements.append(Paragraph(
        f"<b>Objet :</b> {objet}",
        styles["CorpsCourrierEESAG"],
    ))
    elements.append(Spacer(1, 5))

    # Contenu : chaque ligne est échappée pour éviter les balises involontaires.
    contenu = getattr(courrier, "contenu", "") or ""
    paragraphes = re.split(r"\r?\n", contenu)

    for paragraphe in paragraphes:
        paragraphe = paragraphe.strip()
        if paragraphe:
            elements.append(Paragraph(
                _texte_securise(paragraphe),
                styles["CorpsCourrierEESAG"],
            ))
        else:
            elements.append(Spacer(1, 5))

    # Signature
    expediteur = getattr(courrier, "expediteur", None)
    nom_signataire = _nom_complet(expediteur) if expediteur else "___________________"

    fonction_signataire = ""
    if expediteur:
        fonction_signataire = (
            getattr(expediteur, "fonction_bureau_national", "") or ""
        )

        if not fonction_signataire:
            try:
                fonction_signataire = expediteur.get_role_display()
            except (AttributeError, TypeError):
                fonction_signataire = ""

    elements.append(Paragraph(
        "Fait pour servir et valoir ce que de droit."
        "<br/><br/><br/>"
        f"<b>{_texte_securise(fonction_signataire)}</b>"
        "<br/>"
        f"{_texte_securise(nom_signataire)}",
        styles["SignatureEESAG"],
    ))

    doc.build(elements)
    buffer.seek(0)

    nom_fichier = re.sub(
        r"[^A-Za-z0-9._-]+",
        "-",
        str(getattr(courrier, "numero_reference", "courrier")),
    ).strip("-")

    return ContentFile(
        buffer.read(),
        name=f"{nom_fichier or 'courrier'}.pdf",
    )


def texte_exemple(type_courrier: str, nom_cible: str = "") -> str:
    """Fournit un texte initial que l'expéditeur peut personnaliser."""

    if type_courrier == "MISSION":
        return (
            f"Par la présente, la Direction Nationale confie à "
            f"{nom_cible or '[Nom du responsable]'} la mission décrite en objet, "
            "à compter de la date de signature de ce document.\n\n"
            "Le titulaire de cette mission est tenu de rendre compte "
            "régulièrement de ses activités auprès du Bureau National et "
            "de veiller au bon fonctionnement de l'église qui lui est confiée.\n\n"
            "[À personnaliser : détails de la mission, durée et conditions particulières.]"
        )

    if type_courrier == "RECOMMANDATION":
        return (
            f"Nous soussignés attestons que "
            f"{nom_cible or '[Nom complet du membre]'} appartient régulièrement "
            "à notre communauté et y est connu(e) comme membre actif(ve).\n\n"
            "Dans le cadre de son déplacement vers une autre localité, "
            "nous le/la recommandons fraternellement auprès de l'église "
            "destinataire et sollicitons son accueil, son accompagnement "
            "pastoral et son intégration dans la nouvelle communauté.\n\n"
            "Les informations d'identification et d'appartenance sont "
            "complétées à partir du dossier EESAG. Le pasteur peut "
            "personnaliser ce passage avant l'envoi.\n\n"
            "[Ajouter, si nécessaire, le motif ou les circonstances particulières du déplacement.]"
        )

    if type_courrier == "NATIONALE":
        return (
            "Le Bureau National de Coordination porte à votre connaissance "
            "les dispositions et informations précisées dans le présent courrier.\n\n"
            "Les responsables concernés sont invités à prendre les mesures "
            "nécessaires à sa mise en œuvre et à assurer le suivi des "
            "instructions communiquées.\n\n"
            "[À personnaliser par le Coordinateur : contexte, décisions, "
            "instructions, échéances et personnes concernées.]"
        )

    if type_courrier == "NOTE":
        return (
            "La présente note a pour objet de communiquer les informations "
            "et dispositions indiquées ci-dessous.\n\n"
            "[À personnaliser : contexte, mesures à appliquer et date d'entrée en vigueur.]"
        )

    return "[Contenu à rédiger]"
