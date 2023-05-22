import logging
import numpy as np
from flask import Flask, request, jsonify
from fastText import FastTextModel

from utils import get_reaction_name


# set logger
logger = logging.getLogger(__name__)
logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: lines %(lineno)d: %(message)s", filename='fastText.log', encoding='utf-8', level=logging.INFO)

fastText = FastTextModel(logger=logger)

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
app.config['JSON_AS_ASCII'] = False

@app.route('/', methods=["POST"])
def root():
    note = request.get_json()

    fastText.update(note)
    similarity: float = get_similarity(note)

    res = bool(similarity >= np.cos(np.pi / 6))

    if res:
        logger.info(f"note {note['id']} should be renoted: {similarity}")
    else:
        logger.info(f"note {note['id']} should NOT be renoted: {similarity}")

    return jsonify({ "result": res, "similarity": similarity }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0")