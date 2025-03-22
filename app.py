from flask import Flask, render_template, request, jsonify, session
import logging
import os
import openai
import sqlite3
from datetime import datetime

DB_PATH = "chat.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                role TEXT CHECK(role IN ('user', 'assistant')) NOT NULL,
                content TEXT NOT NULL,
                summary TEXT
            )
        ''')
        conn.commit()

def save_message(role: str, content: str, summary: str = None):
    timestamp = datetime.utcnow().isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (timestamp, role, content, summary) VALUES (?, ?, ?, ?)",
            (timestamp, role, content, summary)
        )
        conn.commit()

def update_summary(message_id: int, summary: str):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE messages SET summary = ? WHERE id = ?",
            (summary, message_id)
        )
        conn.commit()

def build_chathistory() -> list[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT role, content, summary
            FROM messages
            ORDER BY timestamp ASC
        """)
        all_messages = cursor.fetchall()

    # Separate recent full messages (last 4 user+assistant)
    full_count = 4
    history = []
    full_messages = all_messages[-full_count:]
    summary_messages = all_messages[:-full_count]

    # Use summaries for older messages
    for role, content, summary in summary_messages:
        if summary:  # Only include if summary exists
            history.append({"role": role, "content": summary})

    # Use full content for the latest 4
    for role, content, _ in full_messages:
        history.append({"role": role, "content": content})

    return history

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Use a secure key in production

# Configure logging (logs errors and conversation to app.log)
logging.basicConfig(filename='app.log', level=logging.INFO,
                    format='%(asctime)s %(levelname)s:%(message)s')

def gpt4o_generate(prompt_or_messages):
    openai.api_key = os.getenv("OPENAI_API_KEY")
    try:
        if isinstance(prompt_or_messages, str):
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt_or_messages}
            ]
        else:
            messages = prompt_or_messages

        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=messages
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error("Error generating response: %s", e)
        return f"Error: Unable to generate a response: {e}"

@app.errorhandler(500)
def internal_error(error):
    logging.error("Server Error: %s", error)
    return jsonify({"error": "Internal server error"}), 500

@app.errorhandler(404)
def not_found_error(error):
    logging.error("Not Found: %s", error)
    return jsonify({"error": "Not found"}), 404

@app.route('/api/message', methods=['POST'])
def message():
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        if not user_message:
            return jsonify({"error": "No message provided"}), 400
        
        # Save user message to DB (no summary yet)
        save_message("user", user_message)

        # Get the ID of the last inserted message
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT last_insert_rowid()")
            user_msg_id = cursor.fetchone()[0]

        # In-memory session management using Flask's session support
        session_id = session.get('session_id')
        if not session_id:
            session_id = os.urandom(16).hex()
            session['session_id'] = session_id
        
        # Summarize the user message
        user_summary_prompt = f"Please summarize this user message in 1–2 sentences: '{user_message}'"
        user_summary = gpt4o_generate(user_summary_prompt)

        # Update the user's message with the summary
        update_summary(user_msg_id, user_summary)

        # Generate bot response via the real GPT-4o integration
        history = build_chathistory()
        history.append({"role": "user", "content": user_message})
        response_text = gpt4o_generate(history)
        # Save assistant message to DB (no summary yet)
        save_message("assistant", response_text)

        # Get the ID of the last inserted message
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT last_insert_rowid()")
            assistant_msg_id = cursor.fetchone()[0]

        # Summarize the assistant message
        assistant_summary_prompt = f"Please summarize this assistant response in 1–2 sentences: '{response_text}'"
        assistant_summary = gpt4o_generate(assistant_summary_prompt)

        # Update the assistant's message with the summary
        update_summary(assistant_msg_id, assistant_summary)

        # Log the conversation to a file
        logging.info("Session %s: user: %s", session_id, user_message)
        logging.info("Session %s: bot: %s", session_id, response_text)

        return jsonify({"response": response_text})
    except Exception as e:
        logging.error("Error in /api/message: %s", e)
        return jsonify({"error": "An error occurred"}), 500

@app.route('/')
def index():
    return render_template("index.html")

init_db()

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)
