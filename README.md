# AI A1 Repo
how to build and run it:
docker build -t ai_gpt_chat_img .
docker run -p 5000:5000 --name ai_gpt_chat_container --env-file .env ai_gpt_chat_img

then open http://localhost:5000/