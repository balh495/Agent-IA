from typing import Any
import sqlite3

class HistoryDatabase:
    """
    La classe HistoryDatabase permet de gérer la base de données SQLite de l'historique des conversations.
    """

    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()

    def init_database(self):

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER,
                role TEXT,
                content TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            )
        """)

        self.conn.commit()

    def get_db_connection(self, streamlit_session_state: Any) -> tuple:
        """
        Gère une connexion SQLite persistante via st.session_state

        Si la connexion n'existe pas dans la session, crée une nouvelle connexion.
        Sinon, utilise la connexion existante.

        Args:
            streamlit_session_state (Any): L'objet de session de Streamlit

        Returns:
            tuple: La connexion et le curseur associé
        """
        if "db_connection" not in streamlit_session_state or streamlit_session_state.db_connection is None:
            streamlit_session_state.db_connection = self.conn
            streamlit_session_state.db_cursor = self.cursor

        return streamlit_session_state.db_connection, streamlit_session_state.db_cursor

    def get_conversations(self) -> list[tuple]:
        """
        Récupère toutes les conversations existantes dans la base de données.

        Returns:
            Une liste de tuples contenant les IDs et les noms des conversations.
        """
        try:
            self.cursor.execute("SELECT id, name FROM conversations")
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Erreur lors de la récupération des conversations : {e}")
            return []

    def create_conversation(self, name: str) -> int:
        """
        Crée une nouvelle conversation dans la base de données.

        Args:
            name (str): Le nom de la conversation

        Returns:
            L'ID de la conversation créée
        """
        try:
            self.cursor.execute("INSERT INTO conversations (name) VALUES (?)", (name,))

            self.conn.commit()

            return self.cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Erreur lors de la création de la conversation : {e}")
            return -1

    def save_message(self, conversation_id: int, role: str, content: str) -> None:
        """
        Sauvegarde un message dans la base de données.

        Args:
            conversation_id (int): L'ID de la conversation
            role (str): Le rôle du message (par exemple, "user" ou "assistant")
            content (str): Le contenu du message
        """
        try:
            self.cursor.execute("INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)", (conversation_id, role, content))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Erreur lors de la sauvegarde du message : {e}")

    def get_messages(self, conversation_id):
        """
        Récupère les messages associés à un ID de conversation donné.

        Args:
            conversation_id (int): L'identifiant de la conversation

        Returns:
            list: Une liste de tuples contenant le rôle et le contenu des messages,
            triés par ordre de timestamp.
        """
        if not conversation_id:
            return []

        try:
            self.cursor.execute("SELECT role, content FROM messages WHERE conversation_id=? ORDER BY timestamp", (conversation_id,))
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Erreur lors de la récupération des messages : {e}")
            return []