import streamlit as st
import ollama

from database_history import HistoryDatabase

# En-tête de la page
st.set_page_config(page_title="AI Chatbot Agent", layout="wide")
st.title("AI Chatbot Agent")

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

# Bouton pour créer une nouvelle conversation
new_convo_id = None
if st.sidebar.button("Nouvelle conversation"):
    new_convo_id = history_db.create_conversation()
    st.session_state.conversation_id = new_convo_id
    st.session_state.chat_history = []

if st.sidebar.button("Supprimer tout"):
    history_db.delete_all_conversations()
    st.rerun()

st.sidebar.markdown("---")

for convo_id, convo_name in conversations:
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

# Show chat history
if 'chat_history' in st.session_state.keys():
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# User prompt
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
            # Prepare the message for the chatbot
            messages = [
                {
                    "role": "system",
                    "content": (
                        "Réponds directement à la question sans inclure ton raisonnement. "
                        "Sois bref et précis. "
                        "Réponds uniquement en français. "
                        "Adopte un style académique. "
                        "Évite toute faute d’orthographe."
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

    if new_convo_id:
        if len(history_db.get_messages(new_convo_id)) == 2:
            conversation_name = prompt if len(prompt) <= 25 else prompt[:22] + "..."
            history_db.update_conversation_name(new_convo_id, conversation_name)
            st.rerun()
    else:
        new_convo_id = history_db.create_conversation()
        st.session_state.conversation_id = new_convo_id
        st.session_state.chat_history = []

        conversation_name = prompt if len(prompt) <= 25 else prompt[:22] + "..."
        history_db.update_conversation_name(new_convo_id, conversation_name)
        st.rerun()
