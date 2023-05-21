import datetime
import fasttext
import logging
import numpy as np
import os
import pandas as pd
import regex

from utils import get_text, get_reaction_name

class FastTextModel:

    def __init__(self, output = "./notes.csv", interval = 10 * 60, logger: logging.Logger | None = None):
        self.save_file = output
        self.interval = interval

        self.datetime = datetime.datetime.now(tz=datetime.timezone.utc)

        self.columns = [ "id", "text", "reactions" ]
        if os.path.exists(self.save_file):
            self.outputs = pd.read_csv(self.save_file, index_col=0)
        else:
            self.outputs: pd.DataFrame = pd.DataFrame([], columns=self.columns)
            self.outputs = self.outputs.set_index(self.columns[0])
        
        
        self.logger = logger
        if self.logger:
            self.logger.info("FastTextModel started")
            
        self.cnt = 0
        self.model = None
        self.update_model()

    def update(self, note: dict):
        if note is not None and note["reactions"]:
            s = [ get_text(note), ' '.join([ f"{get_reaction_name(k)}:{v}" for k, v in note["reactions"].items() if get_reaction_name(k) ]) ]
            self.outputs.loc[note["id"]] = s

            self.cnt += 1

            if len(self.outputs) > 100_000:
                self.outputs = self.outputs.iloc[-100_000:]
            
            if self.cnt > 50_000:
                self.save()
                self.update_model()
    
    def save(self):
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        if (now - self.datetime).seconds > self.interval:
            self.datetime = now
            self.outputs.to_csv(self.save_file, index=True, header=True)
            if self.logger:
                self.logger.info("save data")

    def get_data(self):
        return self.outputs
    
    def _create_lines(self):
        p = regex.compile(r"^([^:]+):(\d+)$")
        results = ''
        for reactions in self.outputs["reactions"]:
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
    
    def update_model(self):
        self.logger.info("update model")

        lines = self._create_lines()

        with open("./reactions.txt", 'w', encoding="utf-8") as f:
            f.write(lines)

        new_model = fasttext.train_unsupervised("./reactions.txt", model="cbow")
        new_model.save_model("model.bin")

        self.model = fasttext.load_model("model.bin")
        self.cnt = 0
    
    def get_word_vector(self, word):
        if word is None:
            dim = self.model.get_dimension()
            return np.zeros(dim)
        
        return self.model.get_word_vector(word)