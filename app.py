from flask import Flask, render_template, request, jsonify, session
import logging
import os
import openai

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Use a secure key in production

# Configure logging (logs errors and conversation to app.log)
logging.basicConfig(filename='app.log', level=logging.INFO,
                    format='%(asctime)s %(levelname)s:%(message)s')

def gpt4o_generate(prompt):
    openai.api_key = os.getenv("OPENAI_API_KEY")
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # or use "gpt-3.5-turbo" if preferred
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
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

        # Generate bot response via the real GPT-4o integration
        response_text = gpt4o_generate(user_message)

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

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)
