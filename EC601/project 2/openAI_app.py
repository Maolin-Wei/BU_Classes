from flask import Flask, render_template, request, jsonify
import openai
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

openai.api_key = os.getenv("OPENAI_API_KEY")
messages = [{"role": "assistant", "content": "You are a helpful assistant with all my questions."}]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/askOpenAI', methods=['POST'])
def ask_openai():
    user_message = request.form['message']
    messages.append({"role": "user", "content": user_message})

    response = get_assistant_response(messages)
    messages.append({"role": "assistant", "content": response})

    return jsonify({"response": response})

def get_assistant_response(messages):
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": m["role"], "content": m["content"]} for m in messages],
    )
    response = completion.choices[0].message.content
    return response

if __name__ == '__main__':
    app.run(debug=True)
