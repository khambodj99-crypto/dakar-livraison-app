import streamlit as st
import pandas as pd
import os
import io
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from auth import check_password

# ==========================================
# 1. CHARGEMENT DES VARIABLES & SÉCURITÉ
# ==========================================
load_dotenv()
# On récupère l'URL Supabase que tu as mise dans le .env
DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)

if not check_password():
    st.stop()

st.set_page_config(page_title="Dakar Livraison PRO", layout="wide")

# ==========================================
# 2. BARRE LATÉRALE (RÉGLAGES)
# ==========================================
st.sidebar.header("⚙️ Configuration Cloud")

# Curseur de commission
taux_com = st.sidebar.slider("Taux de commission (%)", min_value=0, max_value=50, value=10)
taux_decimal = taux_com / 100

st.sidebar.divider()

# --- MODÈLE VIERGE ---
st.sidebar.subheader("📄 Nouveau fichier")
colonnes = ["id", "livreur", "destination", "montant_article", "frais_livraison", "statut"]
df_modele = pd.DataFrame(columns=colonnes)

buffer = io.StringIO()
df_modele.to_csv(buffer, index=False)
csv_modele = buffer.getvalue()

st.sidebar.download_button(
    label="📥 Télécharger le modèle",
    data=csv_modele,
    file_name="modele_livraisons.csv",
    mime="text/csv"
)

# Bouton pour vider la base en ligne (à utiliser avec prudence !)
if st.sidebar.button("🗑️ Vider la base SQL Cloud"):
    try:
        with engine.connect() as conn:
            conn.execute(text("TRUNCATE TABLE suivi_livraisons RESTART IDENTITY"))
            conn.commit()
        st.sidebar.warning("Base Cloud vidée !")
    except Exception as e:
        st.sidebar.error(f"Erreur : {e}")

# ==========================================
# 3. INTERFACE PRINCIPALE
# ==========================================
st.title("🇸🇳 Dashboard Dakar Livraison PRO")
st.write(f"🌐 Connecté au serveur : `{DATABASE_URL.split('@')[1].split(':')[0]}`")

file = st.file_uploader("📂 Charger le fichier des livraisons (CSV)", type="csv")

if file:
    # Lecture du fichier
    df = pd.read_csv(file, encoding='latin-1', sep=None, engine='python')
    
    if 'montant_article' in df.columns:
        # Calculs
        df['commission'] = df['montant_article'] * taux_decimal
        df['net_vendeur'] = df['montant_article'] - df['commission']
        
        # Filtres livreurs
        liste_livreurs = ["Tous"] + list(df['livreur'].unique()) if 'livreur' in df.columns else ["Tous"]
        choix_livreur = st.sidebar.selectbox("🔎 Filtrer par livreur", liste_livreurs)

        df_affiche = df.copy()
        if choix_livreur != "Tous":
            df_affiche = df[df['livreur'] == choix_livreur]

        # KPI
        total_cash = df_affiche['montant_article'].sum()
        total_com = df_affiche['commission'].sum()
        net_patron = total_cash - total_com

        col1, col2, col3 = st.columns(3)
        col1.metric("Cash Collecté", f"{int(total_cash):,} FCFA".replace(",", " "))
        col2.metric(f"Commissions ({taux_com}%)", f"{int(total_com):,} FCFA".replace(",", " "))
        col3.metric("Net à récupérer", f"{int(net_patron):,} FCFA".replace(",", " "))

        st.divider()

        # Affichage et Enregistrement
        c1, c2 = st.columns([1, 1])
        with c1:
            st.subheader("📊 Performance")
            if 'livreur' in df.columns:
                st.bar_chart(df_affiche.groupby('livreur')['montant_article'].sum())
        with c2:
            st.subheader("📋 Aperçu des données")
            st.dataframe(df_affiche, use_container_width=True)

        if st.button("🚀 ENREGISTRER SUR LE CLOUD"):
            try:
                df_affiche.to_sql('suivi_livraisons', con=engine, if_exists='append', index=False)
                st.success("✅ Données envoyées sur Supabase avec succès !")
            except Exception as e:
                st.error(f"❌ Erreur de connexion : {e}")