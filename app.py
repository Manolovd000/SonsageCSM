import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Sondage Sentiers Mayotte",
    layout="wide"
)

# -----------------------------
# CONNEXION GOOGLE SHEETS
# -----------------------------

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope
)

client = gspread.authorize(creds)

sheet = client.open_by_key(
    "1-MXBs9musswmCoITRpYFpWmlZYo_HVdoMlg_-mRO1HQ"
).sheet1


# -----------------------------
# ENVOI DONNÉES
# -----------------------------

def send_to_sheet(data):

    sheet.append_row([
        data["Nom structure"],
        ", ".join(data["Type"]),
        data["Intervention"],
        data["Etat sentiers"],
        data["Gestion sentiers"],
        data["Connaissance"],
        ", ".join(data["Usages"]),
        data["Atouts"],
        ", ".join(data["Freins"]),
        data["SIG"],
        data["Outils"],
        data["Partage de données"],
        data["Attentes"],
        ", ".join(data["Missions prioritaires"]),
        data["Participation commission"],
        data["Contacts pertinents"],
        data["Commentaires"],
        data["Structure"],
        data["Nom"],
        data["Mail"],
        data["Téléphone"]
    ])


# -----------------------------
# TITRE
# -----------------------------

st.title("Sondage – Sentiers, itinéraires et chemins de Mayotte")
st.subheader(
    "Contribution à la structuration d’une commission des sentiers de Mayotte"
)


# -----------------------------
# 1. Profil
# -----------------------------

st.header("1. Profil de la structure")

nom_structure = st.text_input("Nom de la structure")

type_structure = st.multiselect(
    "Type de structure",
    [
        "Collectivité",
        "Service de l’État",
        "Association",
        "Propriétaire foncier",
        "Entreprise - Gestionnaire",
        "Entreprise - Fédération sportive",
        "Autre"
    ]
)

intervention = st.radio(
    "Intervenez-vous dans la gestion des sentiers ?",
    ["Oui", "Non"]
)


# -----------------------------
# 2. Etat des sentiers
# -----------------------------

st.header("2. État des sentiers")

etat_sentiers = st.radio(
    "État global des sentiers",
    ["Très bon", "Bon", "Moyen", "Mauvais", "Très mauvais"]
)

gestion_sentiers = st.radio(
    "Gestion globale des sentiers",
    [
        "Très satisfaisante",
        "Satisfaisante",
        "Moyenne",
        "Insuffisante",
        "Très insuffisante"
    ]
)


# -----------------------------
# 3. Connaissance
# -----------------------------

st.header("3. Connaissance et gestion")

connaissance = st.radio(
    "Niveau de connaissance des sentiers",
    ["Très bon", "Bon", "Moyen", "Faible", "Très faible"]
)

usages = st.multiselect(
    "Usages principaux",
    [
        "Randonnée pédestre",
        "Trail",
        "Accès foncier/ agricole",
        "Tourisme",
        "VTT",
        "Autre"
    ]
)

atouts = st.text_area("Atouts")

freins = st.multiselect(
    "Freins",
    [
        "Manque de moyens financiers",
        "Manque de coordination entre acteurs",
        "Difficultés foncières",
        "Manque de données / connaissance",
        "Manque de moyens humains",
        "Contraintes réglementaires",
        "Difficulté d’entretien réguliers",
        "Autre"
    ]
)


# -----------------------------
# 4. Outils
# -----------------------------

st.header("4. Outils et données")

sig = st.radio(
    "Utilisez-vous des outils SIG ?",
    ["Oui", "Non"]
)

outils = st.text_area("Outils utilisés")

partage = st.radio(
    "Partage de données",
    [
        "Oui librement",
        "Oui sous conditions",
        "Non"
    ]
)


# -----------------------------
# 5. Attentes
# -----------------------------

st.header("5. Attentes et commission")

attentes = st.text_area("Attentes")

missions = st.multiselect(
    "Missions prioritaires",
    [
        "Coordination des acteurs",
        "Suivi et gestion des sentiers",
        "Appui technique",
        "Structuration des données",
        "Recherche de financements",
        "Autre"
    ]
)


# -----------------------------
# 6. Commission
# -----------------------------

st.header("6. Commission")

participation = st.radio(
    "Participation",
    ["Oui", "Non"]
)

contacts = st.text_area(
    "Contacts pertinents"
)


# -----------------------------
# 7. Commentaires
# -----------------------------

st.header("7. Commentaires")

commentaires = st.text_area(
    "Remarques"
)


# -----------------------------
# 8. Contact
# -----------------------------

st.header("8. Contact")

structure_contact = st.text_input("Structure")
nom_contact = st.text_input("Nom / Prénom")
email = st.text_input("Mail")
telephone = st.text_input("Téléphone")


# -----------------------------
# ENVOI
# -----------------------------

if st.button("Soumettre la réponse"):

    data = {

        "Nom structure": nom_structure,
        "Type": type_structure,
        "Intervention": intervention,
        "Etat sentiers": etat_sentiers,
        "Gestion sentiers": gestion_sentiers,
        "Connaissance": connaissance,
        "Usages": usages,
        "Atouts": atouts,
        "Freins": freins,
        "SIG": sig,
        "Outils": outils,
        "Partage de données": partage,
        "Attentes": attentes,
        "Missions prioritaires": missions,
        "Participation commission": participation,
        "Contacts pertinents": contacts,
        "Commentaires": commentaires,
        "Structure": structure_contact,
        "Nom": nom_contact,
        "Mail": email,
        "Téléphone": telephone

    }

    send_to_sheet(data)

    st.success("Réponse envoyée 👍")


# -----------------------------
# VISUALISATION
# -----------------------------

st.header("📊 Visualisation des réponses")

records = sheet.get_all_values()

if len(records) > 1:

    headers = records[0]
    rows = records[1:]

    # nettoyage des en-têtes
    clean_headers = []
    used = set()

    for h in headers:

        h = h.strip()

        if h == "":
            continue

        if h in used:
            continue

        used.add(h)
        clean_headers.append(h)


    rows = [
        r[:len(clean_headers)]
        for r in rows
    ]

    df = pd.DataFrame(
        rows,
        columns=clean_headers
    )


    st.dataframe(df)


    if "Etat sentiers" in df.columns:
        st.subheader("État des sentiers")
        st.bar_chart(
            df["Etat sentiers"].value_counts()
        )


    if "Gestion sentiers" in df.columns:
        st.subheader("Gestion des sentiers")
        st.bar_chart(
            df["Gestion sentiers"].value_counts()
        )


    if "Participation commission" in df.columns:
        st.subheader("Participation commission")
        st.bar_chart(
            df["Participation commission"].value_counts()
        )


else:
    st.info("Aucune réponse pour le moment.")