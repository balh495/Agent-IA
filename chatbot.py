import streamlit as st
import ollama
import time

st.set_page_config(page_title="IA Agent Codeit Chatbot", layout="wide")

st.title("IA Agent - Codeit Chatbot")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Affichage de l'historique des messages
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Prompt utilisateur
prompt = st.chat_input("How can I help you : ")

if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        # Utiliser Ollama pour obtenir une réponse
        response = ollama.chat(
            model="gemma2:2b",
            messages=[{"role": "user", "content": prompt}]
        )
        response_text = response["message"]["content"]

        with st.chat_message("assistant"):
            st.markdown(response_text)

        st.session_state.chat_history.append({"role": "user", "content": prompt})
        st.session_state.chat_history.append({"role": "assistant", "content": response_text})

    except ollama.exceptions.ModelNotFoundError:
        st.error("Le modèle gemma2:2b n'est pas disponible. Veuillez vérifier votre installation Ollama.")
    except Exception as e:
        st.error(f"Une erreur est survenue : {e}")