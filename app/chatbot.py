import streamlit as st
import ollama

from database_history import HistoryDatabase

def init_conversation():
    st.session_state.conversation_id = history_db.create_conversation()
    st.session_state.new_conversation = False

    st.session_state.chat_history = []


def get_conversation_history(conversation_list):
    for convo_id, convo_name in conversation_list:
        if convo_name is not None:
            col1, col2 = st.sidebar.columns([3, 1])
            with col1:
                if st.sidebar.button(f"{convo_name}", key=f"convo_{convo_id}"):
                    st.session_state.conversation_id = convo_id
                    st.session_state.chat_history = [{"role": m[0], "content": m[1]} for m in history_db.get_messages(convo_id)]
                    st.rerun()

            with col2:
                if st.button("❌", key=f"delete_{convo_id}"):
                    history_db.delete_conversation(convo_id)
                    st.write(f"Conversation {convo_name} supprimée")
                    st.rerun()

    st.sidebar.markdown("---")

def get_chat_history():
    if 'chat_history' in st.session_state.keys():
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])


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

# Initialiser d'une nouvelle conversation
if "conversation_id" not in st.session_state:
    init_conversation()

# Bouton pour créer une nouvelle conversation
if st.sidebar.button("Nouvelle conversation"):
    st.session_state.conversation_id = history_db.create_conversation()
    st.session_state.chat_history = []
    st.session_state.new_conversation = True

    # Affichage de l'historique des messages
    get_chat_history()

new_conv_id = st.session_state.conversation_id

# Supprimer l'ensemble des conversations
if st.sidebar.button("Supprimer tout"):
    history_db.delete_all_conversations()
    init_conversation()
    st.rerun()

# Afficher la liste des conversations dans la sidebar
get_conversation_history(conversations)

# Affichage de l'historique des messages
get_chat_history()

# Prompt utilisateur
prompt = st.chat_input("Bonjour, comment puis-je vous aider : ")

if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)

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
                        "Réponds directement, brièvement et précisément en français, avec un style académique et une précieuse rigueure sur l'orthographe."
                        "Tu peux très bien ne pas répondre si tu n'es pas sûr de ta réponse"
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

    if st.session_state.new_conversation:
        if len(history_db.get_messages(new_conv_id)) <= 2:
            conversation_name = prompt if len(prompt) <= 75 else prompt[:72] + "..."
            history_db.update_conversation_name(new_conv_id, conversation_name)

            st.session_state.new_conversation = False
            st.rerun()
    else:
        if len(history_db.get_messages(new_conv_id)) <= 2:
            conversation_name = prompt if len(prompt) <= 75 else prompt[:72] + "..."
            history_db.update_conversation_name(new_conv_id, conversation_name)

            st.rerun()
