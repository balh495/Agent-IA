import streamlit as st
import ollama

from database_history import HistoryDatabase

def init_conversation():
    st.session_state.conversation_id = history_db.create_conversation()
    st.session_state.new_conversation = True

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

    # Affichage de l'historique des messages
    # get_chat_history()

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
                        "Réponds de manière brève et concise, sans inclure de raisonnement."
                        "Réponds uniquement en français avec un soin rigoureux sur l'orthographe."
                        "Tu peux très bien ne pas répondre si tu n'es pas sûr de ta réponse, ne réponds que si tu si tu dispose de ses connaissances."
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
    # if st.session_state.new_conversation:
    if history_db.get_conversation_name(new_conv_id) == "Nouvelle conversation" or history_db.get_conversation_name(new_conv_id) is None:
        if history_db.get_message_count(new_conv_id) >= 2:

            conv_title = ollama.chat(
                model="llama3.2:3b",
                messages=[
                {
                    "role": "system",
                    "content": (
                        "Réponds de manière très brève et concise, sans inclure de raisonnement, en très très peu de mots."
                        "Réponds uniquement en français avec un soin rigoureux sur l'orthographe."
                        "Si le sujet ne renvoit qu'à des salutations ou des questions de bienvenue, ne fais rien et réponds : 'Nouvelle conversation'."
                        "\n".join(history_db.get_message_by_role(new_conv_id, "user"))
                    )
                },
                {"role": "user", "content": "Trouve moi un titre qui résume le sujet centrale des questions de l'utilisateur."}
            ])

            history_db.update_conversation_name(new_conv_id, conv_title["message"]["content"])

            st.session_state.new_conversation = False
            st.rerun()
    # else:
    #     if len(history_db.get_messages(new_conv_id)) <= 2:
    #         conversation_name = prompt if len(prompt) <= 75 else prompt[:72] + "..."
    #         history_db.update_conversation_name(new_conv_id, conversation_name)
    #
    #         st.rerun()
