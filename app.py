from flask import Flask, render_template, request, jsonify, session
import logging
import os
import openai
import sqlite3
from datetime import datetime
import json

DB_PATH = "data/chat.db"

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

def save_message(role: str, content: str, summary: str = None) -> int:
    timestamp = datetime.utcnow().isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (timestamp, role, content, summary) VALUES (?, ?, ?, ?)",
            (timestamp, role, content, summary)
        )
        message_id = cursor.lastrowid
        conn.commit()
        return message_id

def update_summary(message_id: int, summary: str):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE messages SET summary = ? WHERE id = ?",
            (summary, message_id)
        )
        conn.commit()

def build_chathistory_with_stats() -> dict:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT role, content, summary FROM messages ORDER BY timestamp ASC")
        all_messages = cursor.fetchall()

    # Separate recent full messages (last 4 user+assistant)
    full_count = 4
    history = []
    full_messages = all_messages[-full_count:]
    summary_messages = all_messages[:-full_count]

    original_chars = 0
    summarized_chars = 0

    # Use summaries for older messages
    for role, content, summary in summary_messages:
        original_chars += len(content)
        if summary:
            summarized_chars += len(summary)
            history.append({"role": role, "content": summary})
        else:
            summarized_chars += len(content)
            history.append({"role": role, "content": content})  # fallback

    # Use full content for the latest 4
    for role, content, _ in full_messages:
        original_chars += len(content)
        summarized_chars += len(content)
        history.append({"role": role, "content": content})

    return {
        "history": history,
        "original_chars": original_chars,
        "summarized_chars": summarized_chars
    }


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
        
        # In-memory session management using Flask's session support
        session_id = session.get('session_id')
        if not session_id:
            session_id = os.urandom(16).hex()
            session['session_id'] = session_id

        # Save user message
        user_msg_id = save_message("user", user_message)

        # Generate and store summary for user
        user_summary_prompt = f"Please summarize this user message in 1–2 sentences: '{user_message}'"
        user_summary = gpt4o_generate(user_summary_prompt)
        logging.info("Generated user summary: %s", user_summary)
        update_summary(user_msg_id, user_summary)

        # Build history and get char stats
        chat_data = build_chathistory_with_stats()
        history = chat_data["history"]

        logging.info("Final chat history sent to GPT:\n%s", json.dumps(history, indent=2))

        # System instruction for combined response+summary
        system_prompt = (
            "You are a helpful assistant. Respond to the user's message as usual, "
            "but return a JSON object with two fields: 'response' and 'summary'.\n\n"
            "Respond using this format only:\n"
            '{ "response": "...", "summary": "..." }'
        )
        history.insert(0, {"role": "system", "content": system_prompt})

        assistant_reply = gpt4o_generate(history)
        logging.info("Raw assistant reply for JSON parse:\n%s", assistant_reply)

        try:
            if "{" not in assistant_reply or "}" not in assistant_reply:
                raise ValueError("No JSON block found in assistant reply.")
            json_start = assistant_reply.index('{')
            json_content = assistant_reply[json_start:].strip()
            parsed = json.loads(json_content)
            response_text = parsed.get("response", "").strip()
            assistant_summary = parsed.get("summary", "").strip()
        except Exception as e:
            response_text = assistant_reply.strip()
            assistant_summary = "Summary unavailable (JSON parse failed)"
            logging.error("Failed to parse assistant JSON: %s", e)

        logging.info("Parsed assistant summary: %s", assistant_summary)

        assistant_msg_id = save_message("assistant", response_text, assistant_summary)
        logging.info("Saving summary to DB: id=%s, summary=%s", assistant_msg_id, assistant_summary)

        logging.info("Session %s: user: %s", session_id, user_message)
        logging.info("Session %s: bot: %s", session_id, response_text)

        savings = {
            "original_chars": chat_data["original_chars"],
            "summarized_chars": chat_data["summarized_chars"],
            "saved": chat_data["original_chars"] - chat_data["summarized_chars"],
            "percentage": round(
                (chat_data["original_chars"] - chat_data["summarized_chars"]) / chat_data["original_chars"] * 100, 1
            ) if chat_data["original_chars"] else 0
        }
        return jsonify({
            "response": response_text,
            "summary": assistant_summary,
            "savings": savings
        })

    except Exception as e:
        logging.error("Error in /api/message: %s", e)
        return jsonify({"error": "An error occurred"}), 500

@app.route('/')
def index():
    return render_template("index.html")

init_db()

if __name__ == '__main__':
    @app.route('/api/stats', methods=['GET'])
    def stats():
        try:
            chat_data = build_chathistory_with_stats()
            original = chat_data["original_chars"]
            summarized = chat_data["summarized_chars"]
            saved = original - summarized
            percentage = round((saved / original) * 100, 1) if original else 0

            return jsonify({
                "savings": {
                    "original_chars": original,
                    "summarized_chars": summarized,
                    "saved": saved,
                    "percentage": percentage
                }
            })
        except Exception as e:
            logging.error("Error in /api/stats: %s", e)
            return jsonify({"error": "Unable to load stats"}), 500
        
    app.run(host="0.0.0.0", debug=True)
