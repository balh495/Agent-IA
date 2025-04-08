import streamlit as st
import ollama
import os

from database_history import HistoryDatabase
from rag_engine import RAGEngine

########################################################################################################################
# Fonctions utiles
########################################################################################################################

def init_conversation():
    st.session_state.conversation_id = history_db.create_conversation()
    st.session_state.new_conversation = True

    st.session_state.chat_history = []


def get_conversation_history(conversation_list):
    for convo_id, convo_name in conversation_list:
        if convo_name is not None:
            col1, col2 = st.sidebar.columns([4, 1])
            with col1:
                if st.sidebar.button(f"{convo_name}", key=f"convo_{convo_id}"):
                    st.session_state.conversation_id = convo_id
                    st.session_state.chat_history = [{"role": m[0], "content": m[1]} for m in history_db.get_messages(convo_id)]
                    st.rerun()

            with col2:
                if st.button("❌", key=f"delete_{convo_id}"):
                    history_db.delete_conversation(convo_id)
                    st.rerun()

    st.sidebar.markdown("---")

def get_chat_history():
    if 'chat_history' in st.session_state.keys():
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])


def delete_document_from_sidebar(doc_id):
    """Supprime un document à la fois de la sidebar et du vecteur store."""
    doc_path = os.path.join("documents", doc_id)

    # Supprimer le fichier
    if os.path.exists(doc_path):
        os.remove(doc_path)

    # Supprimer du vecteur store
    RAGEngine().delete_document(doc_id)


########################################################################################################################
# Page Streamlit - Initialisation
########################################################################################################################

# En-tête de la page
st.set_page_config(page_title="Agent Chatbot IA", layout="wide")
st.title("Agent Chatbot IA")

# Appliquer un style de lien à un bouton
st.markdown("""
    <style>
    div.stButton > button:first-child {
        background: none;
        border: none;
        color: black;
        text-decoration: none;
        cursor: pointer;
    }
    </style>
""", unsafe_allow_html=True)

# Initialiser la base de données
history_db = HistoryDatabase("./chat_history.db")
history_db.init_database()

# Initialiser l'historique de conversation
conversations = history_db.get_conversations()
conversation_names = [convers_name for _, convers_name in conversations]

########################################################################################################################
# Sidebar
########################################################################################################################
########################################################################################################################
# Historique des conversations
########################################################################################################################

# Bouton pour créer une nouvelle conversation
if st.sidebar.button("Nouvelle conversation"):
    st.session_state.conversation_id = history_db.create_conversation()
    st.session_state.chat_history = []

# Supprimer l'ensemble des conversations
if st.sidebar.button("Supprimer tout"):
    history_db.delete_all_conversations()
    # init_conversation()
    st.rerun()

# Afficher la liste des conversations dans la sidebar
get_conversation_history(conversations)

# Affichage de l'historique des messages
get_chat_history()

########################################################################################################################
# Gestion des documents
########################################################################################################################
os.makedirs("documents", exist_ok=True)
os.makedirs("vectorstore", exist_ok=True)
uploaded_files = st.sidebar.file_uploader("Ajouter un document", type=["pdf", "txt", "docx"], accept_multiple_files=True)

if uploaded_files:
    for file in uploaded_files:
        with open(os.path.join("documents", file.name), "wb") as f:
            f.write(file.getbuffer())
        st.sidebar.success(f"fichier '{file.name}' ajouté!")

st.sidebar.markdown("### 📚 Documents chargés")
use_docs = st.sidebar.checkbox("Utiliser les documents dans la réponse", value=False)

doc_list = os.listdir("documents")
for doc in doc_list:
    col1, col2 = st.sidebar.columns([3, 1])
    with col1:
        if st.sidebar.button(f"{doc}", key=f"doc_{doc}"):
            st.session_state.selected_doc = doc

    with col2:
        if st.sidebar.button("❌", key=f"delete_{doc}"):
            delete_document_from_sidebar(doc)
            st.sidebar.success(f"Document '{doc}' supprimé du système.")
            st.rerun()

if use_docs:
    # Initialiser le moteur de RAG
    with st.spinner("Encodage des documents en cours...", show_time=True):
        rag_engine = RAGEngine()

########################################################################################################################
# Chatbot
########################################################################################################################

# Prompt utilisateur
prompt = st.chat_input("Bonjour, comment puis-je vous aider : ")

if prompt:

    # Initialiser d'une nouvelle conversation
    if "conversation_id" not in st.session_state and "new_conversation" not in st.session_state:
        init_conversation()
    else:
        st.session_state.new_conversation = False

    with st.chat_message("user"):
        st.markdown(prompt)

    rag_chunks = rag_engine.retrieve(query=prompt, k=5) if use_docs else []
    rag_context = "\n".join(rag_chunks)

    def generate_response():
        """Generate a response from the chatbot model and update chat history.

        This function sends a user prompt to the Ollama chatbot model, receives the
        response in streaming mode, and updates the session's chat history with the
        full response. In case of an error, it displays an error message.
        """
        try:
            # Formatage du message
            messages = [
                {
                    "role": "system",
                    "content": (
                        "Réponds de manière brève et concise, sans inclure de raisonnement."
                        "Réponds uniquement en français avec un soin rigoureux sur l'orthographe."
                        "Tu peux très bien ne pas répondre si tu n'es pas sûr de ta réponse, ne réponds que si tu si tu dispose de ses connaissances."
                        "Base toi sur le contexte que je te passe pour répondre. Si tu n'as pas la réponse dans mon contexte tu peux te baser sur tes connaissances fiables, dans quel cas tu dois le préciser que la réponse vient de toi et non de mon contexte"
                        "Voici un contexte extrait de documents pertinents sur lesquels tu dois te baser: \n" + rag_context + "\n" 
                        "Voici le contexte de la conversation (question de l'utilisateur):"
                        "\n".join(history_db.get_message_by_role(st.session_state.conversation_id, "user"))
                    )
                },
                {"role": "user", "content": prompt}
            ]

            # Send the message to Ollama and receive the response in streaming mode
            response = ollama.chat(
                model="llama3.2:3b",
                messages=messages,
                stream=True  # Enable streaming
            )

            full_response = ""
            # Process each chunk of the streaming response
            for chunk in response:
                text_chunk = chunk["message"]["content"]
                full_response += text_chunk
                yield text_chunk  # Stream each text chunk

            # Save chat history after receiving the full response
            history_db.save_message(st.session_state.conversation_id, "user", prompt)
            history_db.save_message(st.session_state.conversation_id, "assistant", full_response)
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            st.session_state.chat_history.append({"role": "assistant", "content": full_response})

        except Exception as e:
            # Display an error message if an exception occurs
            st.error(f"An error occurred : {e}")

    with st.chat_message("assistant"):
        st.write_stream(generate_response())

    # Attribution d'un titre à la conversation
    if st.session_state.new_conversation:
        conv_title = ollama.chat(
            model="llama3.2:1b",
            messages=[
            {
                "role": "system",
                "content": (
                    "\n".join(history_db.get_message_by_role(st.session_state.conversation_id, "user"))
                )
            },
            {"role": "user", "content": "Your task is to generate only a short, affirmative title in French that describes the general topic of the user's request. Do not rephrase, answer, or complete the user's question. The title must not include facts, names, or conclusions, and must never be a question. Output a neutral and abstract description of the topic only."}
        ])

        history_db.update_conversation_name(st.session_state.conversation_id, conv_title["message"]["content"])

        st.session_state.new_conversation = False
        st.rerun()
