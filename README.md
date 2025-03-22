# AI GPT Chat App

This is a simple, responsive web chat interface powered by OpenAI's GPT-4o-mini. It uses Flask for the backend, OpenAI's API for generating responses and summaries, SQLite for memory storage, and Docker for deployment.

---

## 💡 Features

- Real-time chat interface (user ↔ assistant)
- Responsive, system-theme-aware design (light/dark)
- Memory-aware conversation: stores messages and summaries in SQLite
- Summarization using OpenAI: last 4 messages stored in full, older ones condensed
- Dockerized for easy, repeatable deployment
- Logging with timestamps and session tracking (`app.log`)
- Typescript-based frontend for structured, modern development

---

## 🚀 Getting Started

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd <project-folder>
```

### 2. Create `.env` File
```bash
echo "OPENAI_API_KEY=your_key_here" > .env
```

### 3. Build Docker Image
```bash
docker build -t ai_gpt_chat_img .
```

### 4. Run the Container
Create a `data/` folder for the persistent database:
```bash
mkdir -p data
```

Then run the container:
```bash
docker run --rm -p 5000:5000   --name ai_gpt_chat_container   --env-file .env   -v $(pwd)/data:/app/data   -v $(pwd)/app.log:/app/app.log   ai_gpt_chat_img
```

### 5. Open the App
Open [http://localhost:5000](http://localhost:5000) in your browser.

---

## 🧾 Requirements

- Docker
- OpenAI API key (with access to `gpt-4o` or `gpt-4o-mini`)
- NodeJS (for editing/compiling TypeScript frontend)

---

## 📁 Project Structure

```
├── app.py                 # Flask backend with OpenAI + SQLite integration
├── data/                  # Persistent SQLite database (chat.db)
├── templates/
│   └── index.html         # Main frontend HTML layout
├── static/
│   ├── styles.css         # System-theme-aware responsive styles
│   ├── script.ts          # TypeScript chat interaction logic
│   └── script.js          # (auto-generated from TS) Used in the app
├── app.log                # Local log file for session + error logging
├── Dockerfile             # Docker build instructions
├── requirements.txt       # Python dependencies
├── tsconfig.json          # TypeScript configuration
└── README.md              # You're reading it!
```

---

## 📓 Logs & Debugging

- Logs are written to `app.log` (in project root if volume-mounted).
- You can check logs in real time with:

```bash
tail -f app.log
```

- If you're not using volume mounts, you can access logs from inside the running container:

```bash
docker exec -it ai_gpt_chat_container cat /app/app.log
```

---

## 🔄 Resetting the Chat History

To clear all messages:

```bash
sqlite3 data/chat.db
DELETE FROM messages;
.exit
```

Or delete the `data/chat.db` file completely and restart the container.

---

## 🌱 Notes

- The app stores summaries of messages in the database and dynamically builds `chathistory` by combining full recent messages with summaries of older ones.
- GPT responses are returned in structured JSON to include both the reply and a summary in a single call.
- Errors and fallbacks are logged clearly, and summaries are skipped gracefully if something goes wrong.

---

## 🌌 Built with care and clarity
For small, human-scale conversations—remembered gently. 💙
