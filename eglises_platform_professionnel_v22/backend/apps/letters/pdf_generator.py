"""
Génération d'un exemplaire de lettre (mission / recommandation / note) au format A4.
Le texte inséré est un EXEMPLE par défaut — modifiable ensuite directement dans le
champ `contenu` du Courrier (depuis l'API/l'admin) avant régénération du PDF.
"""
import io
from django.core.files.base import ContentFile
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_RIGHT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

NOM_ORGANISATION = "PLATEFORME NATIONALE DE GESTION DES ÉGLISES"
SLOGAN_ORGANISATION = "Bureau National de Coordination"


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="Entete", parent=styles["Heading1"], alignment=TA_CENTER, fontSize=14, spaceAfter=2,
    ))
    styles.add(ParagraphStyle(
        name="SousEntete", parent=styles["Normal"], alignment=TA_CENTER, fontSize=10,
        textColor=colors.HexColor("#444444"), spaceAfter=16,
    ))
    styles.add(ParagraphStyle(
        name="Reference", parent=styles["Normal"], alignment=TA_RIGHT, fontSize=10, spaceAfter=20,
    ))
    styles.add(ParagraphStyle(
        name="TitreObjet", parent=styles["Heading2"], alignment=TA_CENTER,
        fontSize=13, spaceBefore=10, spaceAfter=20, underlineWidth=1,
    ))
    styles.add(ParagraphStyle(
        name="CorpsTexte", parent=styles["Normal"], alignment=TA_JUSTIFY, fontSize=11,
        leading=17, spaceAfter=14,
    ))
    styles.add(ParagraphStyle(
        name="Signature", parent=styles["Normal"], alignment=TA_RIGHT, fontSize=11, spaceBefore=40,
    ))
    return styles


def generer_pdf_courrier(courrier) -> ContentFile:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=2.2 * cm, bottomMargin=2.2 * cm, leftMargin=2.5 * cm, rightMargin=2.5 * cm,
    )
    styles = _styles()
    elements = []

    # --- En-tête ---
    elements.append(Paragraph(NOM_ORGANISATION, styles["Entete"]))
    elements.append(Paragraph(SLOGAN_ORGANISATION, styles["SousEntete"]))

    ligne = Table([[""]], colWidths=[16.5 * cm], rowHeights=[0.03 * cm])
    ligne.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 1.2, colors.HexColor("#1a3c5e"))]))
    elements.append(ligne)
    elements.append(Spacer(1, 16))

    # --- Référence / lieu / date ---
    elements.append(Paragraph(
        f"{courrier.lieu_emission}, le {courrier.date_emission.strftime('%d/%m/%Y')}<br/>"
        f"N° {courrier.numero_reference}",
        styles["Reference"],
    ))

    # --- Titre ---
    titre_map = {
        "MISSION": "LETTRE DE MISSION",
        "RECOMMANDATION": "LETTRE DE RECOMMANDATION",
        "NOTE": "NOTE DE SERVICE",
    }
    elements.append(Paragraph(titre_map.get(courrier.type_courrier, "COURRIER"), styles["TitreObjet"]))

    # --- Destinataire ---
    if courrier.eglise_destinataire:
        elements.append(Paragraph(
            f"<b>À l'attention de :</b> Église « {courrier.eglise_destinataire.nom} » "
            f"— {courrier.eglise_destinataire.commune or courrier.eglise_destinataire.district}",
            styles["CorpsTexte"],
        ))
    if courrier.membre_concerne:
        elements.append(Paragraph(
            f"<b>Concernant :</b> {courrier.membre_concerne.prenom} {courrier.membre_concerne.nom} "
            f"(Identifiant : {courrier.membre_concerne.identifiant})",
            styles["CorpsTexte"],
        ))

    elements.append(Paragraph(f"<b>Objet :</b> {courrier.objet}", styles["CorpsTexte"]))
    elements.append(Spacer(1, 10))

    # --- Corps du texte (exemple, modifiable) ---
    for paragraphe in courrier.contenu.split("\n"):
        if paragraphe.strip():
            elements.append(Paragraph(paragraphe.strip(), styles["CorpsTexte"]))

    # --- Signature ---
    nom_signataire = f"{courrier.expediteur.prenom} {courrier.expediteur.nom}" if courrier.expediteur else "___________________"
    fonction_signataire = courrier.expediteur.fonction_bureau_national if (
        courrier.expediteur and courrier.expediteur.fonction_bureau_national
    ) else courrier.expediteur.get_role_display() if courrier.expediteur else ""
    elements.append(Paragraph(
        f"Fait pour servir et valoir ce que de droit.<br/><br/><br/>"
        f"<b>{fonction_signataire}</b><br/>{nom_signataire}",
        styles["Signature"],
    ))

    doc.build(elements)
    buffer.seek(0)
    return ContentFile(buffer.read(), name=f"{courrier.numero_reference.replace('/', '-')}.pdf")


def texte_exemple(type_courrier: str, nom_cible: str = "") -> str:
    """Renvoie un exemple de contenu à personnaliser ensuite (comme demandé par l'utilisateur)."""
    if type_courrier == "MISSION":
        return (
            f"Par la présente, la Direction Nationale confie à {nom_cible or '[Nom du responsable]'} "
            "la mission pastorale décrite en objet, à compter de la date de signature de ce document.\n\n"
            "Le titulaire de cette mission est tenu de rendre compte régulièrement de ses activités "
            "auprès du Bureau National et de veiller au bon fonctionnement de l'église qui lui est confiée.\n\n"
            "[Texte à modifier : détails de la mission, durée, conditions particulières...]"
        )
    if type_courrier == "RECOMMANDATION":
        return (
            f"Nous soussignés attestons que {nom_cible or '[Nom du membre]'} est un membre actif et "
            "en règle au sein de notre communauté.\n\n"
            "Nous le/la recommandons auprès de qui de droit pour toute démarche nécessitant une "
            "attestation de bonne conduite et d'appartenance à notre église.\n\n"
            "[Texte à modifier selon le contexte précis de la recommandation.]"
        )
    return "[Contenu à rédiger]"
