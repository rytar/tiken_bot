import logging
from flask import Flask, request, jsonify
from fastText import FastTextModel


# set logger
logger = logging.getLogger(__name__)
logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: lines %(lineno)d: %(message)s", filename="./fastText.log", encoding="utf-8", level=logging.INFO)

fastText = FastTextModel(logger=logger)


app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

@app.route('/', methods=["POST"])
def root():
    query = request.get_json()

    action = query["action"]

    if action == "update":
        note = query["note"]
        
        logger.info(f"{action}: {note['id']}")

        fastText.update(note)

        return jsonify({ "result": True }), 200
    
    if action == "get_word_vector":
        word = query["word"]
        
        logger.info(f"{action}: {word}")

        return jsonify({ "result": fastText.get_word_vector(word).tolist() }), 200
    
    if action == "get_dimension":
        logger.info(f"{action}")
        
        return jsonify({ "result": fastText.model.get_dimension() }), 200

    return jsonify({ "result": "no action" }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0")