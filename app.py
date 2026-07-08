from __future__ import annotations

import re

import gspread
import pandas as pd
import plotly.express as px
import streamlit as st
from google.oauth2.service_account import Credentials


# =============================================================================
# CONFIGURATION
# =============================================================================

SHEET_ID = "1-MXBs9musswmCoITRpYFpWmlZYo_HVdoMlg_-mRO1HQ"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Séparateur utilisé pour stocker les réponses multi-choix dans une seule
# cellule Google Sheets. Conservé identique à la version d'origine (", ")
# pour rester compatible avec les réponses déjà enregistrées dans le sheet.
MULTISELECT_SEP = ", "

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

TYPE_STRUCTURE_OPTIONS = [
    "Collectivité",
    "Service de l'État",
    "Association",
    "Propriétaire foncier",
    "Gestionnaire",
    "Fédération sportive",
    "Entreprise",
    "Autre",
]

USAGES_OPTIONS = [
    "Randonnée pédestre",
    "Trail",
    "Accès foncier/ agricole",
    "Tourisme",
    "VTT",
    "Autre",
]

FREINS_OPTIONS = [
    "Manque de moyens financiers",
    "Manque de coordination entre acteurs",
    "Difficultés foncières",
    "Manque de données / connaissance",
    "Manque de moyens humains",
    "Contraintes réglementaires",
    "Difficulté d'entretien réguliers",
    "Autre",
]

GESTION_ACTIONS_OPTIONS = [
    "Entretien / débroussaillage",
    "Balisage et signalétique",
    "Sécurisation des passages dangereux",
    "Gestion des accès (barrières, autorisations)",
    "Surveillance et suivi de l'état des sentiers",
    "Relations avec les propriétaires fonciers",
    "Collecte de données / cartographie",
    "Nettoyage et ramassage des déchets",
    "Sensibilisation et communication auprès du public",
    "Valorisation du territoire",
    "Gestion des conflits d'usage",
    "Travaux de génie écologique (érosion, drainage)",
    "Aucune action de gestion actuellement",
    "Autre",
]

MISSIONS_OPTIONS = [
    "Coordination des acteurs",
    "Entretien des sentiers",
    "Valorisation territoriale",
    "Production de données",
    "Animation territoriale",
    "Autre",
]

# Ordre des colonnes tel qu'écrit dans le Google Sheet (ne pas changer l'ordre
# sans mettre à jour l'en-tête du sheet en conséquence).
# "Actions de gestion" est ajoutée en toute fin de liste : cela ajoute une
# nouvelle colonne à droite dans le sheet sans décaler aucune colonne
# existante ni aucune ligne déjà enregistrée.
SHEET_COLUMNS = [
    "Nom structure", "Type", "Intervention", "Etat sentiers", "Gestion sentiers",
    "Connaissance", "Usages", "Atouts", "Freins", "SIG", "Outils",
    "Partage de données", "Attentes", "Missions prioritaires",
    "Participation groupe de travail", "Contacts pertinents", "Commentaires",
    "Structure", "Nom", "Mail", "Téléphone", "Actions de gestion",
]

st.set_page_config(page_title="Sondage Sentiers Mayotte", layout="wide")


# =============================================================================
# STYLE / PALETTE
# =============================================================================

# Palette douce et cohérente, inspirée de tons naturels (végétation, terre,
# lagon) — utilisée pour l'ensemble des graphiques du dashboard, afin que
# tous les visuels partagent la même identité visuelle.
PALETTE = [
    "#5C7A5C",  # vert sauge foncé
    "#8FA998",  # vert sauge clair
    "#C97B63",  # terracotta
    "#D4B996",  # sable
    "#6E8CA0",  # bleu lagon
    "#A99985",  # taupe
    "#E0B589",  # ocre clair
    "#3E6259",  # teal profond
]

CHART_FONT = dict(family="Helvetica, Arial, sans-serif", size=13, color="#3E3A35")


def inject_custom_css() -> None:
    """Harmonise quelques éléments d'interface (bouton principal) avec la
    palette utilisée dans les graphiques, pour une cohérence visuelle globale."""
    st.markdown(
        f"""
        <style>
        div.stButton > button:first-child {{
            background-color: {PALETTE[0]};
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.5em 1.6em;
            font-weight: 500;
        }}
        div.stButton > button:first-child:hover {{
            background-color: {PALETTE[7]};
            color: white;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def style_figure(fig, title: str | None = None):
    """Applique un style visuel cohérent (fond transparent, police douce,
    grille discrète) à tous les graphiques Plotly du dashboard."""
    fig.update_layout(
        title=title,
        font=CHART_FONT,
        title_font=dict(size=16, color="#3E3A35"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=50 if title else 20, b=10),
        hoverlabel=dict(bgcolor="white", font_size=13, font_family=CHART_FONT["family"]),
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(0,0,0,0.06)", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(0,0,0,0.06)", zeroline=False)
    return fig


# =============================================================================
# CONNEXION GOOGLE SHEETS (mise en cache pour éviter de ré-authentifier /
# ré-ouvrir le classeur à chaque interaction utilisateur)
# =============================================================================

@st.cache_resource(show_spinner=False)
def get_worksheet():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=SCOPES
    )
    client = gspread.authorize(creds)
    return client.open_by_key(SHEET_ID).sheet1


@st.cache_data(ttl=30, show_spinner=False)
def load_responses() -> pd.DataFrame:
    """Charge les réponses existantes sous forme de DataFrame propre.

    Renvoie un DataFrame vide (mais aux bonnes colonnes) s'il n'y a pas
    encore de réponse, afin que le reste du dashboard n'ait jamais à
    deviner si `df` existe.
    """
    records = get_worksheet().get_all_values()

    if len(records) <= 1:
        return pd.DataFrame(columns=SHEET_COLUMNS)

    headers, rows = records[0], records[1:]

    clean_headers, used = [], set()
    for h in headers:
        h = h.strip()
        if h and h not in used:
            used.add(h)
            clean_headers.append(h)

    rows_clean = [r[: len(clean_headers)] for r in rows]
    return pd.DataFrame(rows_clean, columns=clean_headers)


def append_response(data: dict) -> None:
    get_worksheet().append_row([
        data["Nom structure"],
        MULTISELECT_SEP.join(data["Type"]),
        data["Intervention"],
        data["Etat sentiers"],
        data["Gestion sentiers"],
        data["Connaissance"],
        MULTISELECT_SEP.join(data["Usages"]),
        data["Atouts"],
        MULTISELECT_SEP.join(data["Freins"]),
        data["SIG"],
        data["Outils"],
        data["Partage de données"],
        data["Attentes"],
        MULTISELECT_SEP.join(data["Missions prioritaires"]),
        data["Participation groupe de travail"],
        data["Contacts pertinents"],
        data["Commentaires"],
        data["Structure"],
        data["Nom"],
        data["Mail"],
        data["Téléphone"],
        MULTISELECT_SEP.join(data["Actions de gestion"]),
    ])
    # Les nouvelles données doivent apparaître immédiatement dans le
    # dashboard, sans attendre l'expiration du cache.
    load_responses.clear()


# =============================================================================
# VALIDATION
# =============================================================================

# Champs multi-choix pour lesquels une option "Autre" existe, avec le libellé
# à utiliser dans les messages d'erreur si la précision manque.
AUTRE_FIELDS = {
    "Type": "type de structure",
    "Usages": "usage",
    "Freins": "frein",
    "Missions prioritaires": "mission prioritaire",
    "Actions de gestion": "action de gestion",
}


def validate(data: dict) -> list[str]:
    """Retourne la liste des messages d'erreur (vide si tout est valide)."""
    errors = []

    if not data["Nom structure"].strip():
        errors.append("Le nom de la structure est obligatoire.")

    if not data["Type"]:
        errors.append("Merci de sélectionner au moins un type de structure.")

    for field, label in AUTRE_FIELDS.items():
        if "Autre" in data[field] and not data[f"{field}_autre"].strip():
            errors.append(f"Merci de préciser votre réponse « Autre » pour « {label} ».")

    if not data["Nom"].strip():
        errors.append("Le nom du contact est obligatoire.")

    if not data["Mail"].strip():
        errors.append("L'adresse mail est obligatoire.")
    elif not EMAIL_REGEX.match(data["Mail"].strip()):
        errors.append("L'adresse mail saisie ne semble pas valide.")

    if data["Téléphone"].strip() and not re.match(r"^[\d\s+().-]{6,}$", data["Téléphone"].strip()):
        errors.append("Le numéro de téléphone saisie ne semble pas valide.")

    return errors


def merge_autre(selection: list[str], precision: str) -> list[str]:
    """Remplace l'entrée littérale "Autre" par "Autre : <précision>" si fournie."""
    if "Autre" in selection and precision.strip():
        return [item for item in selection if item != "Autre"] + [f"Autre : {precision.strip()}"]
    return selection


def finalize_data(raw: dict) -> dict:
    """Construit le dict final (celui envoyé au sheet) à partir des données brutes du formulaire."""
    return {
        "Nom structure": raw["Nom structure"],
        "Type": merge_autre(raw["Type"], raw["Type_autre"]),
        "Intervention": raw["Intervention"],
        "Etat sentiers": raw["Etat sentiers"],
        "Gestion sentiers": raw["Gestion sentiers"],
        "Connaissance": raw["Connaissance"],
        "Usages": merge_autre(raw["Usages"], raw["Usages_autre"]),
        "Atouts": raw["Atouts"],
        "Freins": merge_autre(raw["Freins"], raw["Freins_autre"]),
        "SIG": raw["SIG"],
        "Outils": raw["Outils"],
        "Partage de données": raw["Partage de données"],
        "Attentes": raw["Attentes"],
        "Missions prioritaires": merge_autre(raw["Missions prioritaires"], raw["Missions prioritaires_autre"]),
        "Participation groupe de travail": raw["Participation groupe de travail"],
        "Contacts pertinents": raw["Contacts pertinents"],
        "Commentaires": raw["Commentaires"],
        "Structure": raw["Structure"],
        "Nom": raw["Nom"],
        "Mail": raw["Mail"],
        "Téléphone": raw["Téléphone"],
        "Actions de gestion": merge_autre(raw["Actions de gestion"], raw["Actions de gestion_autre"]),
    }


# =============================================================================
# FORMULAIRE
# =============================================================================

def multiselect_with_autre(
    label: str, options: list[str], key_prefix: str, suffix: int, short_label: str | None = None
) -> tuple[list[str], str]:
    """Affiche un multiselect et, si "Autre" est sélectionné, fait apparaître
    immédiatement un champ de précision juste en dessous.

    `short_label` permet d'utiliser un intitulé court pour le champ de
    précision quand `label` est une question longue et détaillée.
    """
    selection = st.multiselect(label, options, key=f"{key_prefix}_{suffix}")
    precision = ""
    if "Autre" in selection:
        precision = st.text_input(
            f"↳ Précisez « Autre » — {short_label or label}",
            key=f"{key_prefix}_autre_{suffix}",
        )
    return selection, precision


def render_form() -> None:
    st.title("Sondage – Sentiers, itinéraires et chemins de Mayotte")
    st.subheader(
        "Contribution à la structuration d'un groupe de travail dédié aux sentiers de Mayotte"
    )
    st.caption("Les champs marqués d'un * sont obligatoires.")

    # Pas de st.form ici : on a besoin que le champ "Précisez" apparaisse
    # immédiatement quand "Autre" est coché, ce qu'un st.form ne permet pas
    # (il ne relance le script qu'au clic sur "Envoyer"). Le compteur
    # `submission_count` sert de suffixe de clé pour tous les widgets : en
    # l'incrémentant après un envoi réussi, on force Streamlit à recréer des
    # widgets tout neufs (donc vides) pour la personne suivante.
    suffix = st.session_state.get("submission_count", 0)

    if st.session_state.pop("just_submitted", False):
        st.success("Réponse envoyée avec succès, merci pour votre contribution !")
        st.balloons()

    st.header("1. Profil de la structure")
    nom_structure = st.text_input(
        "Nom de votre structure ou organisation *", key=f"nom_structure_{suffix}"
    )
    type_structure, type_autre = multiselect_with_autre(
        "Quel type de structure représentez-vous ? *",
        TYPE_STRUCTURE_OPTIONS,
        "type_structure",
        suffix,
        short_label="type de structure",
    )
    intervention = st.radio(
        "Votre structure intervient-elle directement dans la gestion des sentiers "
        "(entretien, balisage, autorisation d'accès, etc.) ?",
        ["Oui", "Non"],
        key=f"intervention_{suffix}",
    )

    st.header("2. État des sentiers")
    etat_sentiers = st.radio(
        "Selon vous, quel est l'état physique général des sentiers de Mayotte "
        "(praticabilité, entretien, balisage) ?",
        ["Très bon", "Bon", "Moyen", "Mauvais", "Très mauvais"],
        key=f"etat_sentiers_{suffix}",
    )
    gestion_sentiers = st.radio(
        "Comment évaluez-vous la gestion actuelle des sentiers à l'échelle de "
        "Mayotte (coordination entre acteurs, suivi, entretien) ?",
        ["Très satisfaisante", "Satisfaisante", "Moyenne", "Insuffisante", "Très insuffisante"],
        key=f"gestion_sentiers_{suffix}",
    )

    st.header("3. Connaissance et gestion")
    st.caption(
        "Les questions suivantes portent sur les sentiers dont votre structure a la "
        "charge : gestion, entretien, foncier, autorisation d'accès, balisage, etc."
    )
    connaissance = st.radio(
        "Quel est votre niveau de connaissance de vos sentiers (tracés, foncier, état) ?",
        ["Très bon", "Bon", "Moyen", "Faible", "Très faible"],
        key=f"connaissance_{suffix}",
    )
    usages, usages_autre = multiselect_with_autre(
        "Quels sont les principaux usages constatés sur vos sentiers ?",
        USAGES_OPTIONS,
        "usages",
        suffix,
        short_label="usages",
    )
    actions_gestion, actions_gestion_autre = multiselect_with_autre(
        "Quelles sont vos actions de gestion en lien avec vos sentiers ?",
        GESTION_ACTIONS_OPTIONS,
        "actions_gestion",
        suffix,
        short_label="actions de gestion",
    )
    atouts = st.text_area("Quels sont les atouts de la gestion de vos sentiers ?", key=f"atouts_{suffix}")
    freins, freins_autre = multiselect_with_autre(
        "Quels sont les principaux freins à la gestion de vos sentiers ?",
        FREINS_OPTIONS,
        "freins",
        suffix,
        short_label="freins",
    )

    st.header("4. Outils et données")
    sig = st.radio(
        "Utilisez-vous des outils de cartographie numérique (SIG) pour vos sentiers ?",
        ["Oui", "Non"],
        key=f"sig_{suffix}",
    )
    outils = st.text_area(
        "Si oui, lesquels ? (ex : QGIS, ArcGIS, applications GPS, etc.)", key=f"outils_{suffix}"
    )
    partage = st.radio(
        "Seriez-vous disposé à partager les données concernant vos sentiers (tracés, "
        "inventaires, cartographies) avec les autres membres du groupe de travail ?",
        ["Oui librement", "Oui sous conditions", "Non"],
        key=f"partage_{suffix}",
    )

    st.header("5. Vos attentes vis-à-vis du groupe de travail")
    st.caption(
        "Ces questions portent sur ce que vous attendez du futur groupe de travail : "
        "missions, objectifs, priorités."
    )
    attentes = st.text_area(
        "Quelles sont vos attentes vis-à-vis d'une démarche collective de gestion "
        "des sentiers à Mayotte ?",
        key=f"attentes_{suffix}",
    )
    missions, missions_autre = multiselect_with_autre(
        "Quelles missions souhaiteriez-vous voir portées en priorité par le futur "
        "groupe de travail ?",
        MISSIONS_OPTIONS,
        "missions",
        suffix,
        short_label="missions prioritaires",
    )

    st.header("6. Structuration du groupe de travail")
    st.caption(
        "Ces questions portent sur la mise en place concrète du groupe de travail : "
        "votre participation et les acteurs à y associer."
    )
    participation = st.radio(
        "Souhaitez-vous participer activement aux travaux du groupe de travail sur "
        "la gestion des sentiers de Mayotte ?",
        ["Oui", "Non", "Peut-être"],
        key=f"participation_{suffix}",
    )
    contacts = st.text_area(
        "Connaissez-vous d'autres structures ou personnes qu'il serait utile "
        "d'associer à ce groupe de travail ?",
        key=f"contacts_{suffix}",
    )
    commentaires = st.text_area(
        "Avez-vous d'autres remarques ou suggestions à partager ?", key=f"commentaires_{suffix}"
    )

    st.header("7. Vos coordonnées")
    st.caption(
        "Merci d'indiquer vos coordonnées en tant que personne ayant rempli ce "
        "questionnaire pour la structure indiquée en section 1."
    )
    structure = st.text_input(
        "Fonction / poste occupé au sein de la structure (facultatif)",
        key=f"structure_{suffix}",
    )
    nom = st.text_input("Nom et prénom *", key=f"nom_{suffix}")
    mail = st.text_input("Adresse mail *", key=f"mail_{suffix}")
    telephone = st.text_input("Téléphone (facultatif)", key=f"telephone_{suffix}")

    submitted = st.button("Envoyer", key=f"submit_{suffix}")

    if not submitted:
        return

    raw = {
        "Nom structure": nom_structure,
        "Type": type_structure,
        "Type_autre": type_autre,
        "Intervention": intervention,
        "Etat sentiers": etat_sentiers,
        "Gestion sentiers": gestion_sentiers,
        "Connaissance": connaissance,
        "Usages": usages,
        "Usages_autre": usages_autre,
        "Actions de gestion": actions_gestion,
        "Actions de gestion_autre": actions_gestion_autre,
        "Atouts": atouts,
        "Freins": freins,
        "Freins_autre": freins_autre,
        "SIG": sig,
        "Outils": outils,
        "Partage de données": partage,
        "Attentes": attentes,
        "Missions prioritaires": missions,
        "Missions prioritaires_autre": missions_autre,
        "Participation groupe de travail": participation,
        "Contacts pertinents": contacts,
        "Commentaires": commentaires,
        "Structure": structure,
        "Nom": nom,
        "Mail": mail,
        "Téléphone": telephone,
    }

    errors = validate(raw)
    if errors:
        for err in errors:
            st.error(err)
        return

    data = finalize_data(raw)

    with st.spinner("Envoi de votre réponse en cours..."):
        try:
            append_response(data)
        except Exception:
            st.error(
                "Une erreur est survenue lors de l'envoi de votre réponse. "
                "Merci de réessayer dans quelques instants."
            )
            return

    # Incrémenter le suffixe force Streamlit à recréer tous les widgets du
    # formulaire avec des clés inédites, donc vides : c'est ce qui "remet à
    # zéro" le formulaire pour la personne suivante.
    st.session_state["submission_count"] = suffix + 1
    st.session_state["just_submitted"] = True
    st.rerun()


# =============================================================================
# DASHBOARD
# =============================================================================

def bar_chart(
    series: pd.Series,
    value_name: str,
    label_name: str,
    title: str | None = None,
    as_percent: bool = False,
    vertical: bool = False,
) -> None:
    """Diagramme en bâtons stylé (horizontal par défaut, vertical si demandé)
    à partir d'une Series de comptages, avec la palette douce du dashboard."""
    data = series.reset_index()
    data.columns = [label_name, value_name]

    if vertical:
        fig = px.bar(
            data, x=label_name, y=value_name, text=value_name,
            color=label_name, color_discrete_sequence=PALETTE,
        )
        fig.update_yaxes(title="Pourcentage (%)" if as_percent else "Nombre de réponses")
        fig.update_xaxes(title="")
    else:
        fig = px.bar(
            data, x=value_name, y=label_name, orientation="h", text=value_name,
            color=label_name, color_discrete_sequence=PALETTE,
        )
        fig.update_xaxes(title="Pourcentage (%)" if as_percent else "Nombre de réponses")
        fig.update_yaxes(title="")

    fig.update_traces(
        texttemplate="%{text:.0f}%" if as_percent else "%{text}",
        textposition="outside",
        marker_line_width=0,
        opacity=0.9,
    )
    fig.update_layout(showlegend=False, bargap=0.35)
    style_figure(fig, title)
    st.plotly_chart(fig, use_container_width=True)


def exploded_counts(df: pd.DataFrame, column: str, normalize: bool = False) -> pd.Series:
    return (
        df[column]
        .dropna()
        .str.split(MULTISELECT_SEP)
        .explode()
        .str.strip()
        .replace("", pd.NA)
        .dropna()
        .value_counts(normalize=normalize)
    )


def render_summary(df: pd.DataFrame) -> None:
    st.subheader("📌 Synthèse générale")

    total_reponses = len(df)
    total_structures = df["Nom structure"].nunique() if "Nom structure" in df.columns else 0
    taux_participation = (
        (df["Participation groupe de travail"] == "Oui").mean() * 100
        if "Participation groupe de travail" in df.columns and total_reponses > 0
        else 0
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Réponses reçues", total_reponses)
    col2.metric("Structures représentées", total_structures)
    col3.metric("Participation au groupe de travail", f"{taux_participation:.0f}%")


def render_missions_priority(df: pd.DataFrame) -> None:
    st.markdown("**Objectifs prioritaires du groupe de travail**")

    if "Missions prioritaires" not in df.columns or df.empty:
        st.info("Aucune donnée disponible pour les objectifs prioritaires.")
        return

    top = exploded_counts(df, "Missions prioritaires", normalize=True).head(3) * 100
    if top.empty:
        st.info("Aucune donnée disponible pour les objectifs prioritaires.")
        return

    # 1/5 : vertical
    bar_chart(top, "Pourcentage", "Objectif", as_percent=True, vertical=True)


def render_profil_structures(df: pd.DataFrame) -> None:
    st.divider()
    st.subheader("Profil des structures")

    if "Type" not in df.columns or df.empty:
        st.info("Aucune donnée disponible sur le profil des structures.")
        return

    counts = exploded_counts(df, "Type")
    if counts.empty:
        st.info("Aucune donnée disponible sur le profil des structures.")
        return

    # 2/5 : horizontal
    bar_chart(counts, "Nombre", "Type", title="Répartition des types de structures", vertical=False)


def render_etat_sentiers(df: pd.DataFrame) -> None:
    st.divider()
    st.subheader("Perception de l'état des sentiers")

    if "Etat sentiers" not in df.columns or df.empty:
        st.info("Aucune donnée disponible sur l'état des sentiers.")
        return

    data = df["Etat sentiers"].value_counts().reset_index()
    data.columns = ["Etat", "Nombre"]

    fig = px.pie(
        data, names="Etat", values="Nombre", hole=0.45,
        color_discrete_sequence=PALETTE,
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        marker=dict(line=dict(color="white", width=2)),
    )
    style_figure(fig, "Etat global des sentiers")
    st.plotly_chart(fig, use_container_width=True)


def render_gestion(df: pd.DataFrame) -> None:
    if "Gestion sentiers" not in df.columns or df.empty:
        return

    counts = df["Gestion sentiers"].value_counts()

    # 3/5 : vertical
    bar_chart(counts, "Nombre", "Gestion", title="Perception de la gestion actuelle", vertical=True)


def render_freins(df: pd.DataFrame) -> None:
    st.divider()
    st.subheader("Principaux freins identifiés")

    if "Freins" not in df.columns or df.empty:
        st.info("Aucune donnée disponible sur les freins identifiés.")
        return

    counts = exploded_counts(df, "Freins")
    if counts.empty:
        st.info("Aucune donnée disponible sur les freins identifiés.")
        return

    # 4/5 : horizontal
    bar_chart(counts, "Nombre", "Frein", title="Classement des freins", vertical=False)


def render_missions_detail(df: pd.DataFrame) -> None:
    if "Missions prioritaires" not in df.columns or df.empty:
        return

    st.divider()
    st.subheader("Missions prioritaires pour le groupe de travail")

    counts = exploded_counts(df, "Missions prioritaires")
    if counts.empty:
        return

    # 5/5 : vertical
    bar_chart(counts, "Nombre", "Mission", title="Attentes prioritaires", vertical=True)


def render_table(df: pd.DataFrame) -> None:
    st.divider()
    st.subheader("📋 Données détaillées")
    st.caption(
        "Les coordonnées personnelles (mail, téléphone) ne sont pas affichées "
        "ici pour préserver la confidentialité des répondants."
    )

    colonnes_sensibles = [c for c in ["Mail", "Téléphone"] if c in df.columns]
    df_public = df.drop(columns=colonnes_sensibles)

    st.dataframe(df_public, use_container_width=True, height=500)


def render_dashboard() -> None:
    st.header("📊 Tableau de bord - Sentiers de Mayotte")

    with st.spinner("Chargement des réponses..."):
        df = load_responses()

    if df.empty:
        st.info("Aucune réponse n'a encore été enregistrée pour le moment.")
        return

    render_summary(df)
    render_missions_priority(df)
    render_profil_structures(df)
    render_etat_sentiers(df)
    render_gestion(df)
    render_freins(df)
    render_missions_detail(df)
    render_table(df)


# =============================================================================
# MAIN
# =============================================================================

def main() -> None:
    inject_custom_css()
    render_form()
    render_dashboard()


if __name__ == "__main__":
    main()

