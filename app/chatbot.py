import streamlit as st
import ollama

from database_history import HistoryDatabase

# Configurer Streamlit
st.set_page_config(page_title="AI Chatbot Agent", layout="wide")
st.title("AI Chatbot Agent")

# Initialiser la base de données
history_db = HistoryDatabase("./chat_history.db")
history_db.init_database()

# Sidebar pour sélectionner une conversation
st.sidebar.header("💬 Conversations")
conversations = history_db.get_conversations()
conversation_names = [c[1] for c in conversations]

# Evite une erreur si aucune conversation n'existe
selected_convo = st.sidebar.selectbox("Sélectionner une conversation", conversation_names, index=0 if conversations else None, key="selected_convo")

new_convo_name = st.sidebar.text_input("Nouvelle conversation", key="new_convo")
if st.sidebar.button("➕ Créer"):
    if new_convo_name.strip():  # Vérifier que ce n'est pas vide
        convo_id = history_db.create_conversation(new_convo_name)
        st.session_state.conversation_id = convo_id
        st.session_state.chat_history = []
        st.rerun()

if selected_convo:
    convo_id = next((c[0] for c in conversations if c[1] == selected_convo), None)
    st.session_state.conversation_id = convo_id
    st.session_state.chat_history = [{"role": m[0], "content": m[1]} for m in history_db.get_messages(convo_id)]
else:
    st.session_state.chat_history = []

# Show chat history
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