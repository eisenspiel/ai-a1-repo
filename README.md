# AI GPT Chat App

This is a simple, responsive web chat interface powered by OpenAI's GPT-4o-mini. It uses Flask for the backend, OpenAI's API for message generation, and Docker for deployment.

## 💡 Features

- Real-time chat interface
- Responsive design with mobile support
- Light/Dark theme support (follows system settings)
- Fixed input bar with animated typing indicator
- User and AI message bubbles styled and aligned
- Dockerized for easy deployment

## 🚀 Getting Started

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd <project-folder>
```

### 2. Create `.env` File
Create a file named `.env` in the root folder with your OpenAI API key:
```
OPENAI_API_KEY=your_key_here
```

### 3. Build Docker Image
```bash
docker build -t ai_gpt_chat_img .
```

### 4. Run the Container
```bash
docker run -p 5000:5000 --name ai_gpt_chat_container --env-file .env ai_gpt_chat_img
```

### 5. Open in Browser
Visit [http://localhost:5000](http://localhost:5000)

## 🧾 Requirements

- Docker
- OpenAI API key (with access to `gpt-4o`)

## 📁 Project Structure

```
├── app.py               # Flask app with OpenAI integration
├── templates/
│   └── index.html       # Main chat UI
├── static/
│   ├── styles.css       # Responsive & theme-aware styles
│   └── script.js        # Frontend logic (input, message rendering)
├── requirements.txt     # Python dependencies
├── Dockerfile           # Build instructions for Docker
└── README.md            # You're reading it!
```

## 🛡️ Notes

- Logs are stored in `app.log` inside the container.
- In production, consider hiding logs or using a logging service.