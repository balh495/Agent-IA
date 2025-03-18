import streamlit as st
import ollama

st.set_page_config(page_title="AI Chatbot Agent - JO", layout="wide")

st.title("AI Chatbot Agent - JO")

if "chat_history" not in st.session_state:
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
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            st.session_state.chat_history.append({"role": "assistant", "content": full_response})

        except Exception as e:
            # Display an error message if an exception occurs
            st.error(f"An error occurred : {e}")


    with st.chat_message("assistant"):
        st.write_stream(generate_response())