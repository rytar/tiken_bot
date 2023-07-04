import asyncio
import datetime
import fasttext
import json
import logging
import numpy as np
import os
import pandas as pd
import regex

from utils import get_text, get_reaction_name


with open("../config.json") as f:
    config = json.loads(f.read())

DEBUG = config["DEBUG"]

class FastTextModel:

    def __init__(self, output = "./notes.csv", interval = 10 * 60, logger: logging.Logger | None = None):
        self.save_file = output
        self.interval = interval

        self.datetime = datetime.datetime.now(tz=datetime.timezone.utc)
        self.max_notes = 100_000
        self.save_timing = 50_000

        self.columns = [ "id", "text", "reactions" ]
        if os.path.exists(self.save_file):
            self.outputs = pd.read_csv(self.save_file, index_col=0, engine="python", on_bad_lines="warn")
            self.outputs = self.outputs.iloc[:self.max_notes]
        else:
            self.outputs: pd.DataFrame = pd.DataFrame([], columns=self.columns)
            self.outputs = self.outputs.set_index(self.columns[0])
        
        
        self.logger = logger
        if self.logger:
            self.logger.info("FastTextModel started")
            
        self.cnt = 0
        self.model = None
        asyncio.run(self.update_model())

    def update(self, note: dict):
        if note is not None and note["reactions"]:
            s = [ get_text(note), ' '.join([ f"{get_reaction_name(k)}:{v}" for k, v in note["reactions"].items() if get_reaction_name(k) ]) ]
            if note["id"] in self.outputs.index:
                self.outputs = self.outputs.drop(index=note["id"])
                
            self.outputs.loc[note["id"]] = s

            self.cnt += 1

            if len(self.outputs) > self.max_notes:
                self.outputs = self.outputs.iloc[-self.max_notes:]
            
            if self.cnt > self.save_timing:
                self.save()

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_in_executor(None, self.update_model)
    
    def save(self):
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        if (now - self.datetime).seconds > self.interval:
            self.datetime = now
            self.outputs.to_csv(self.save_file, index=True, header=True)
            if self.logger:
                self.logger.info("save data")

    def get_data(self):
        return self.outputs
    
    def __create_lines(self):
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
    
    async def update_model(self):
        self.cnt = 0

        if self.logger:
            self.logger.info("update model")

        lines = self.__create_lines()

        with open("./reactions.txt", 'w', encoding="utf-8") as f:
            f.write(lines)

        new_model = fasttext.train_unsupervised("./reactions.txt", model="cbow")
        new_model.save_model("./model.bin")

        self.model = fasttext.load_model("./model.bin")
    
    def get_word_vector(self, word):
        if word is None:
            dim = self.model.get_dimension()
            return np.zeros(dim)
        
        return self.model.get_word_vector(word)