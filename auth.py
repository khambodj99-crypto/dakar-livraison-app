# Contenu de auth.py
import streamlit as st

def check_password():
    """Retourne True si l'utilisateur a saisi le bon mot de passe."""

    def password_entered():
        """Vérifie si le mot de passe saisi est correct."""
        if st.session_state["password"] == "Dakar2026": # Modifie le mot de passe ici
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # On ne garde pas le MDP en mémoire
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # Affichage du formulaire de connexion
        st.text_input("Identifiant", key="username")
        st.text_input("Mot de passe", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        # Si le mot de passe est faux
        st.text_input("Identifiant", key="username")
        st.text_input("Mot de passe", type="password", on_change=password_entered, key="password")
        st.error("😕 Identifiant ou mot de passe incorrect.")
        return False
    else:
        # Mot de passe correct
        return True