import os
import logging

from flask import Flask, request, jsonify, render_template, session
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY")
if not app.secret_key:
    raise RuntimeError("Set the FLASK_SECRET_KEY App Service application setting.")

ENDPOINT = os.environ.get(
    "AZURE_AI_PROJECT_ENDPOINT",
    "https://msftfoundry202912.services.ai.azure.com/api/projects/AI-project1",
)
AGENT_NAME = os.environ.get("AZURE_AI_AGENT_NAME", "luna-agent")

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))


@app.get("/")
def home():
    return render_template("index.html")


@app.post("/chat")
def chat():
    payload = request.get_json(silent=True) or {}
    message = payload.get("message", "")
    if not isinstance(message, str) or not message.strip():
        return jsonify(error="Please enter a message."), 400
    if len(message) > 10000:
        return jsonify(error="Message is too long (maximum 10,000 characters)."), 400

    try:
        with (
            DefaultAzureCredential() as credential,
            AIProjectClient(
                endpoint=ENDPOINT,
                credential=credential,
                allow_preview=True,
            ) as project_client,
        ):
            openai_client = project_client.get_openai_client(agent_name=AGENT_NAME)

            conversation_id = session.get("conversation_id")
            if not conversation_id:
                conversation = openai_client.conversations.create()
                conversation_id = conversation.id
                session["conversation_id"] = conversation_id

            response = openai_client.responses.create(
                conversation=conversation_id,
                input=[{"role": "user", "content": message.strip()}],
            )
            return jsonify(reply=response.output_text)

    except Exception:
        app.logger.exception("Foundry agent request failed")
        return jsonify(
            error=(
                "The request to Microsoft Foundry failed. Check App Service "
                "logs, the project endpoint, agent name, and managed-identity "
                "permissions. Detailed errors are kept in server logs."
            )
        ), 502


@app.post("/new-conversation")
def new_conversation():
    session.pop("conversation_id", None)
    return jsonify(status="ok")


@app.get("/health")
def health():
    return jsonify(status="healthy")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
