import os

from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv
from google import genai

from chatbot_config import CHATBOT_NAME, SYSTEM_PROMPT


load_dotenv()

app = Flask(__name__)

MODEL_NAME = "gemini-3.1-flash-lite"


def create_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY was not found. Check your .env file."
        )

    if api_key == "your_gemini_api_key_here":
        raise RuntimeError(
            "Replace the placeholder GEMINI_API_KEY in .env with your real API key."
        )

    return genai.Client(api_key=api_key)


@app.route("/")
def home():
    return render_template(
        "index.html",
        chatbot_name=CHATBOT_NAME
    )


@app.route("/api/chat", methods=["POST"])
def chat():

    try:
        data = request.get_json(silent=True)

        if not data:
            return jsonify({
                "error": "Invalid JSON request."
            }), 400

        message = data.get("message", "").strip()
        history = data.get("history", [])

        if not message:
            return jsonify({
                "error": "Message cannot be empty."
            }), 400

        if not isinstance(history, list):
            history = []

        history = history[-12:]

        conversation = []

        for item in history:

            if not isinstance(item, dict):
                continue

            role = item.get("role")
            content = item.get("content")

            if role not in ["user", "model"]:
                continue

            if not isinstance(content, str):
                continue

            content = content.strip()

            if not content:
                continue

            conversation.append(
                f"{role.upper()}: {content}"
            )

        previous_conversation = "\n".join(
            conversation
        )

        prompt = f"""
{SYSTEM_PROMPT}

PREVIOUS CONVERSATION:
{previous_conversation or "No previous conversation."}

CURRENT USER MESSAGE:
{message}

Answer the user according to the instructions above.
"""

        print("\n" + "=" * 60)
        print("Sending request to Gemini...")
        print("Model:", MODEL_NAME)
        print("=" * 60)

        client = create_gemini_client()

        chat = client.chats.create(
            model=MODEL_NAME
        )

        response = chat.send_message(
            prompt
        )

        reply = response.text

        if not reply:
            raise RuntimeError(
                "Gemini returned an empty response."
            )

        print("Gemini response received successfully.")
        print("=" * 60)

        return jsonify({
            "reply": reply.strip()
        })


    except Exception as error:

        print("\n" + "=" * 60)
        print("GEMINI / CHAT ERROR")
        print(type(error).__name__)
        print(str(error))
        print("=" * 60 + "\n")

        return jsonify({
            "error": (
                "Backend error: "
                + str(error)
            )
        }), 500


if __name__ == "__main__":

    port = int(
        os.getenv("PORT", "5000")
    )

    print("\n" + "=" * 60)
    print("Foodie AI is starting...")
    print("Model:", MODEL_NAME)
    print("URL: http://127.0.0.1:" + str(port))
    print("=" * 60 + "\n")

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )