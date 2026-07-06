import streamlit as st
import pandas as pd

st.set_page_config(page_title="Sondage Sentiers Mayotte", layout="wide")

# -----------------------------
# TITRE
# -----------------------------
st.title("Sondage – Sentiers, itinéraires et chemins de Mayotte")
st.subheader("Contribution à la structuration d’une commission des sentiers de Mayotte")

# Stockage temporaire
if "responses" not in st.session_state:
    st.session_state.responses = []

# -----------------------------
# 1. Profil de la structure
# -----------------------------
st.header("1. Profil de la structure")

nom_structure = st.text_input("Nom de la structure")

type_structure = st.multiselect(
    "Type de structure (plusieurs choix possibles)",
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
# 2. État des lieux des sentiers
# -----------------------------
st.header("2. État des lieux des sentiers")

etat_sentiers = st.radio(
    "Comment évaluez-vous l’état global des sentiers à Mayotte ?",
    ["Très bon", "Bon", "Moyen", "Mauvais", "Très mauvais"]
)

gestion_sentiers = st.radio(
    "Comment évaluez-vous la gestion globale des sentiers à Mayotte ?",
    ["Très satisfaisante", "Satisfaisante", "Moyenne", "Insuffisante", "Très insuffisante"]
)

# -----------------------------
# 3. Connaissance et gestion des sentiers
# -----------------------------
st.header("3. Connaissance et gestion des sentiers")

connaissance = st.radio(
    "Comment évaluez-vous votre niveau de connaissance et de référencement des sentiers sur votre territoire ?",
    ["Très bon", "Bon", "Moyen", "Faible", "Très faible"]
)

usages = st.multiselect(
    "Quels sont les usages principaux des sentiers ? (plusieurs choix possibles)",
    [
        "Randonnée pédestre",
        "Trail",
        "Accès foncier/ agricole",
        "Tourisme",
        "VTT",
        "Autre"
    ]
)

atouts = st.text_area("Quels sont vos atouts concernant la gestion des sentiers ?")

freins = st.multiselect(
    "Quels sont les principaux freins rencontrés ? (plusieurs choix possibles)",
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
# 4. Outils et données
# -----------------------------
st.header("4. Outils et données")

sig = st.radio(
    "Utilisez-vous des outils de cartographie ou SIG ?",
    ["Oui", "Non"]
)

outils = st.text_area(
    "Quels outils utilisez-vous pour connaître ou gérer les sentiers ?"
)

partage = st.radio(
    "Seriez-vous disposé à partager vos données relatives aux sentiers (SIG ou autres) dans un cadre partenarial ?",
    ["Oui librement", "Oui sous conditions", "Non"]
)

# -----------------------------
# 6. Attentes et commission
# -----------------------------
st.header("6. Attentes et commission")

attentes = st.text_area(
    "Quelles sont vos attentes vis-à-vis de la création d’une commission des sentiers ?"
)

missions = st.multiselect(
    "Selon vous, quelles missions devraient être prioritaires pour cette commission ?",
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
# 7. Commission
# -----------------------------
st.header("7. Commission")

participation = st.radio(
    "Souhaitez-vous participer à cette commission ?",
    ["Oui", "Non"]
)

contacts = st.text_area(
    "Quelles structures ou contacts seraient pertinents à associer à cette commission ? (mail si possible)"
)

# -----------------------------
# 8. Commentaires
# -----------------------------
st.header("8. Commentaires")

commentaires = st.text_area(
    "Remarques ou propositions complémentaires"
)

# -----------------------------
# 9. Contact (facultatif)
# -----------------------------
st.header("9. Contact (facultatif)")

structure_contact = st.text_input("Structure")
nom_contact = st.text_input("Nom / Prénom")
email = st.text_input("Adresse mail")
telephone = st.text_input("Téléphone")

# -----------------------------
# Bouton de soumission
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
        "Freins": freins,
        "SIG": sig,
        "Partage données": partage,
        "Participation commission": participation
    }

    st.session_state.responses.append(data)
    st.success("Réponse enregistrée !")

# -----------------------------
# VISUALISATION TEMPS RÉEL
# -----------------------------
st.header("📊 Visualisation des réponses en temps réel")

if st.session_state.responses:
    df = pd.DataFrame(st.session_state.responses)

    st.dataframe(df)

    st.subheader("Répartition de l’état des sentiers")
    st.bar_chart(df["Etat sentiers"].value_counts())

    st.subheader("Répartition de la gestion des sentiers")
    st.bar_chart(df["Gestion sentiers"].value_counts())

    st.subheader("Participation à la commission")
    st.bar_chart(df["Participation commission"].value_counts())

else:
    st.info("Aucune réponse pour le moment.")
