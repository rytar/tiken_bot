import numpy as np
from flask import Flask, request, jsonify
from fastText import FastTextModel

from utils import get_reaction_name

fastText = FastTextModel()

def get_reaction_vector(note: dict):
    total: int = np.sum(list(note["reactions"].values()))
    results = np.zeros(fastText.model.get_dimension(), dtype=np.float32)

    for reaction, cnt in note["reactions"].items():
        name = get_reaction_name(reaction)
        results += fastText.get_word_vector(name) * int(cnt) / total
    
    return results

def get_similarity(note: dict):
    total: int = np.sum(list(note["reactions"].values()))

    positive_reactions = [
        "tasukaru",
        "igyo",
        "naruhodo",
        "arigato",
        "benri",
        "sitteokou",
        "otoku"
    ]

    negative_reactions = [
        "fakenews",
        "kaibunsyo_itadakimasita",
        "kusa",
        "thinking_face",
        "sonnakotonai",
        "dosukebe",
    ]

    reaction_vec = get_reaction_vector(note)

    target_vec = fastText.get_word_vector("tiken")
    target_norm = np.linalg.norm(target_vec)

    for except_reaction in negative_reactions:
        target_vec -= fastText.get_word_vector(except_reaction) / len(negative_reactions) * 1.2

    for add_reaction in positive_reactions:
        target_vec += fastText.get_word_vector(add_reaction) / len(positive_reactions) * 2.5

    target_vec *= target_norm / np.linalg.norm(target_norm)

    score = reaction_vec @ target_vec / (np.linalg.norm(reaction_vec) * np.linalg.norm(target_vec))

    return score * (total - 1) / total


app = Flask(__name__)

@app.route('/', methods=["POST"])
def root():
    note = request.form.get("note", {}, type=dict)

    fastText.update(note)
    similarity: float = get_similarity(note)
    res: bool = get_similarity(note) >= np.cos(np.pi / 6)

    return jsonify({"result": res, "similarity": similarity}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0")