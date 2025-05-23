from flask import Flask, request, jsonify
import torch
import random
import json
from model import NeuralNet
from ntk_utils import bag_of_words, tokenize
import numpy as np
from flask_cors import CORS
app = Flask(__name__)
CORS(app)

# Load the intents and model data
with open('intents.json', 'r') as f:
    intents = json.load(f)

FILE = "data.pth"
data = torch.load(FILE)

input_size = data['input_size']
hidden_size = data['hidden_size']
output_size = data['output_size']
all_words = data['all_words']
tags = data['tags']

# Load the model
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = NeuralNet(input_size, hidden_size, output_size).to(device)
model.load_state_dict(data['model_state'])
model.eval()

@app.route('/', methods=['GET', 'HEAD'])  # Allow both GET and HEAD methods
def index():
    return jsonify({"message": "Chatbot API is running"}), 200

@app.route('/chat', methods=['GET', 'POST'], strict_slashes=False)
def chat():
    if request.method == 'GET':
        return jsonify({"message": "Use POST method with 'message' key."}), 200

    try:
        req_data = request.get_json()
        print("Received request:", req_data)

        sentence = req_data.get("message")
        if not sentence:
            return jsonify({"error": "Missing message"}), 400

        # Preprocess input
        sentence_tokens = tokenize(sentence)
        X = bag_of_words(sentence_tokens, all_words)
        X = X.reshape(1, X.shape[0])
        X = torch.from_numpy(X).to(device)

        # Model prediction
        output = model(X)
        _, predicted = torch.max(output, dim=1)
        tag = tags[predicted.item()]

        probs = torch.softmax(output, dim=1)
        prob = probs[0][predicted.item()]

        if prob.item() > 0.75:
            for intent in intents['intents']:
                if tag == intent['tag']:
                    response = random.choice(intent['responses'])
                    return jsonify({"bot": response})
        else:
            return jsonify({"bot": "I don't understand..."})
    except Exception as e:
        print("Error:", str(e))
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


import os

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
