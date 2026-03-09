import os
from flask import Flask, request, jsonify, render_template
from google import genai
from dotenv import load_dotenv

from rag import rag_system

load_dotenv()

app = Flask(__name__)

# Create Gemini client
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# In-memory conversation store
conversation_history = {}
MAX_HISTORY_LENGTH = 5


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/api/chat', methods=['POST'])
def chat():

    data = request.json

    if not data or 'message' not in data or 'sessionId' not in data:
        return jsonify({"error": "Missing 'message' or 'sessionId'"}), 400

    session_id = data['sessionId']
    user_message = data['message']

    if not api_key:
        return jsonify({
            "reply": "System Error: GEMINI_API_KEY missing.",
            "tokensUsed": 0,
            "retrievedChunks": 0
        }), 500

    # 1️⃣ Retrieve docs from RAG
    retrieved_docs, err = rag_system.retrieve(user_message, top_k=3)

    if err:
        return jsonify({"error": err}), 500

    chunks_count = len(retrieved_docs)

    # 2️⃣ Build context
    context = ""

    if chunks_count > 0:
        context = "Relevant Knowledge Base Information:\n"

        for i, doc in enumerate(retrieved_docs):
            context += f"\n--- Document {i+1} ---\n{doc['chunk']}\n"
    else:
        context = "No relevant information found in the knowledge base."

    # 3️⃣ Conversation history
    if session_id not in conversation_history:
        conversation_history[session_id] = []

    history = conversation_history[session_id]

    # Convert history into prompt text
    history_text = ""
    for msg in history:
        role = "User" if msg["role"] == "user" else "Assistant"
        history_text += f"{role}: {msg['content']}\n"

    # 4️⃣ Build prompt
    prompt = f"""
You are a helpful and accurate customer support assistant.

Answer the user's question using the provided Knowledge Base.

If the information is not in the knowledge base, say:
"I don't have enough information based on our documentation."

{context}

Conversation History:
{history_text}

User Question:
{user_message}

Answer:
"""

    try:

        # 5️⃣ Gemini generation
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        reply_content = response.text

        # Update history
        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": reply_content})

        # Limit history
        if len(history) > MAX_HISTORY_LENGTH * 2:
            conversation_history[session_id] = history[-(MAX_HISTORY_LENGTH * 2):]

        return jsonify({
            "reply": reply_content,
            "tokensUsed": 0,
            "retrievedChunks": chunks_count
        })

    except Exception as e:
        print("LLM Error:", e)
        return jsonify({"error": str(e)}), 500


import os

if __name__ == "__main__":
    # Get the port from environment variable (Render sets this automatically)
    port = int(os.environ.get("PORT", 5000))
    
    # Run Flask app on all interfaces (0.0.0.0) for deployment, debug mode for local testing
    app.run(host="0.0.0.0", port=port, debug=True)