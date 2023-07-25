import asyncio
import fasttext
import json
import logging
import numpy as np
import os
import pandas as pd
import regex
import time

from utils import fire_and_forget, get_reaction_name, get_text


with open("./config.json") as f:
    config = json.loads(f.read())

DEBUG = config["DEBUG"]

class FastTextModel:

    def __init__(self, output = "./data/notes.csv", interval = 10 * 60):
        self.save_file = output
        self.interval = interval

        self.max_notes = 100_000
        self.save_timing = 50_000

        self.processing = False

        self.columns = [ "id", "text", "reactions" ]
        if os.path.exists(self.save_file):
            self.notes = pd.read_csv(self.save_file, index_col=0, engine="python", on_bad_lines="warn")
            self.notes = self.notes.iloc[:self.max_notes]
        else:
            self.notes: pd.DataFrame = pd.DataFrame([], columns=self.columns)
            self.notes = self.notes.set_index(self.columns[0])
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("FastTextModel started")

        self.reaction_path = "./data/reactions.txt"
            
        self.cnt = 0
        self.model_path = "./data/model.bin"
        if os.path.exists(self.model_path):
            self.model = fasttext.load_model(self.model_path)
        else:
            self.model = None
            asyncio.run(self.update_model())

    @fire_and_forget
    def update(self, note: dict):
        if note is not None and note["reactions"]:
            while self.processing: time.sleep(0.1)

            self.notes.loc[note["id"]] = [ get_text(note), ' '.join([ f"{get_reaction_name(k)}:{v}" for k, v in note["reactions"].items() if get_reaction_name(k) ]) ]
            self.cnt += 1
            
            if self.cnt > self.save_timing:
                self.cnt = 0
                self.save()
                asyncio.run(self.update_model)
            
            self.processing = False
    
    def save(self):
        self.notes.to_csv(self.save_file, index=True, header=True)
        self.logger.info("save data")

    def get_data(self):
        return self.notes
    
    def __create_lines(self):
        p = regex.compile(r"^([^:]+):(\d+)$")
        results = ''
        for reactions in self.notes["reactions"]:
            matches = [ p.fullmatch(reaction) for reaction in reactions.split(' ') ]
            groups = [ m.groups() for m in matches if m ]

            reaction_list = []

            for reaction, cnt in groups:
                reaction_list.extend([ reaction ] * int(cnt))
            
            if len(reaction_list) < 2: continue

            np.random.shuffle(reaction_list)
            res = ' '.join(reaction_list)

            results += res + '\n'
        
        return results
    
    async def update_model(self):
        self.cnt = 0

        self.logger.info("update model")

        lines = self.__create_lines()

        with open(self.reaction_path, 'w', encoding="utf-8") as f:
            f.write(lines)

        new_model = fasttext.train_unsupervised(self.reaction_path, model="cbow")
        new_model.save_model(self.model_path)

        self.model = fasttext.load_model(self.model_path)
    
    def get_word_vector(self, word):
        if word is None:
            dim = self.model.get_dimension()
            return np.zeros(dim)
        
        return self.model.get_word_vector(word)
