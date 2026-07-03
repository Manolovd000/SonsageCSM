import streamlit as st
import pandas as pd
import os

FILE = "reponses_sentiers.csv"

st.set_page_config(page_title="Sondage Sentiers Mayotte", layout="wide")

# Charger données
if os.path.exists(FILE):
    df = pd.read_csv(FILE)
else:
    df = pd.DataFrame()

# TITRE
st.title("Sondage – Sentiers, itinéraires et chemins de Mayotte")
st.subheader("Contribution à la structuration d’une commission des sentiers de Mayotte")

st.divider()

# -----------------------
# FORMULAIRE
# -----------------------
with st.form("formulaire"):

    st.header("1. Profil")
    nom_structure = st.text_input("Nom de la structure")

    type_structure = st.multiselect("Type de structure", [
        "Collectivité","Service de l’État","Association",
        "Propriétaire foncier","Entreprise",
        "Gestionnaire","Fédération sportive","Autre"
    ])

    intervention = st.radio("Intervenez-vous dans la gestion ?", ["Oui", "Non"])

    st.header("2. État des lieux")
    etat = st.radio("État des sentiers", ["Très bon","Bon","Moyen","Mauvais","Très mauvais"])
    gestion = st.radio("Gestion globale", ["Très satisfaisante","Satisfaisante","Moyenne","Insuffisante","Très insuffisante"])

    st.header("3. Connaissance")
    connaissance = st.radio("Niveau de connaissance", ["Très bon","Bon","Moyen","Faible","Très faible"])

    usages = st.multiselect("Usages", [
        "Randonnée","Trail","Agricole","Tourisme","VTT","Autre"
    ])

    freins = st.multiselect("Freins", [
        "Financiers","Coordination","Foncier","Données",
        "Humains","Réglementaires","Entretien","Autre"
    ])

    st.header("4. Outils")
    sig = st.radio("Utilisez-vous un SIG ?", ["Oui","Non"])
    partage = st.radio("Partage de données", ["Oui librement","Oui sous conditions","Non"])

    st.header("5. Commission")
    participation = st.radio("Souhaitez-vous participer ?", ["Oui","Non"])

    submit = st.form_submit_button("Envoyer")

# -----------------------
# ENREGISTREMENT
# -----------------------
if submit:
    new_data = pd.DataFrame([{
        "structure": nom_structure,
        "type": ", ".join(type_structure),
        "intervention": intervention,
        "etat": etat,
        "gestion": gestion,
        "connaissance": connaissance,
        "usages": ", ".join(usages),
        "freins": ", ".join(freins),
        "sig": sig,
        "partage": partage,
        "participation": participation
    }])

    df = pd.concat([df, new_data], ignore_index=True)
    df.to_csv(FILE, index=False)

    st.success("Réponse enregistrée !")

# -----------------------
# 📊 ANALYSE TEMPS RÉEL
# -----------------------

st.divider()
st.header("📊 Tableau de bord des résultats")

if not df.empty:

    # KPI
    col1, col2, col3 = st.columns(3)
    col1.metric("Nombre de réponses", len(df))
    col2.metric("Acteurs gestionnaires (%)",
                round((df["intervention"] == "Oui").mean()*100,1))
    col3.metric("Favorables à la commission (%)",
                round((df["participation"] == "Oui").mean()*100,1))

    st.divider()

    # -------- ETAT SENTIERS
    st.subheader("État des sentiers")
    etat_counts = df["etat"].value_counts()
    st.bar_chart(etat_counts)

    # -------- GESTION
    st.subheader("Qualité de gestion")
    gestion_counts = df["gestion"].value_counts()
    st.bar_chart(gestion_counts)

    # -------- CONNAISSANCE
    st.subheader("Niveau de connaissance des sentiers")
    connaissance_counts = df["connaissance"].value_counts()
    st.bar_chart(connaissance_counts)

    # -------- FREINS (important PDIPR)
    st.subheader("Freins principaux")

    freins_series = df["freins"].dropna().str.split(", ")
    freins_exploded = freins_series.explode()
    freins_counts = freins_exploded.value_counts()

    st.bar_chart(freins_counts)

    # -------- USAGES
    st.subheader("Usages des sentiers")

    usages_series = df["usages"].dropna().str.split(", ")
    usages_exploded = usages_series.explode()
    usages_counts = usages_exploded.value_counts()

    st.bar_chart(usages_counts)

    # -------- SIG
    st.subheader("Utilisation SIG")
    st.bar_chart(df["sig"].value_counts())

    # -------- PARTAGE DONNEES
    st.subheader("Partage de données")
    st.bar_chart(df["partage"].value_counts())

    # -------- TABLE COMPLETE
    st.subheader("Table des réponses")
    st.dataframe(df)

else:
    st.info("Aucune réponse enregistrée pour le moment")