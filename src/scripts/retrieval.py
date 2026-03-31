from transformers import AutoModelForCausalLM, AutoTokenizer
import torch,json
from sentence_transformers import SentenceTransformer
import json
import pandas as pd
import faiss
import numpy as np

sentence_model = SentenceTransformer("all-MiniLM-L6-v2")

class Retriever:
    def __init__(self):
        self.model_name = "numind/NuExtract-tiny-v1.5"
        self.device = "cpu"
        self.model = AutoModelForCausalLM.from_pretrained(self.model_name, torch_dtype=torch.bfloat16, trust_remote_code=True).to(self.device).eval()
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, trust_remote_code=True)
        self.sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
        #self.df = pd.read_parquet('wlkg/data/entities_def.parquet')
        self.df = pd.read_parquet('data/entities_def.parquet')


    def extract_knowledge(self, template, text, max_length=10_000, max_new_tokens=4_000):
        model = self.model
        tokenizer = self.tokenizer
        
        prompt = f"""<|input|>\n### Template:\n{template}\n### Text:\n{text}\n\n<|output|>"""
        outputs = []
        with torch.no_grad():
            
            batch_encodings = tokenizer(prompt, return_tensors="pt", truncation=True, padding=True, max_length=max_length).to(model.device)
            pred_ids = model.generate(**batch_encodings, max_new_tokens=max_new_tokens)
            outputs += tokenizer.batch_decode(pred_ids, skip_special_tokens=True)
            

        return outputs[0].split("<|output|>")[1]
    
    def link(self, entity, type,k=3):
        if type == 'work':
            index = faiss.read_index('data/faiss_db/text/work.faiss')
        elif type == 'person':
            index = faiss.read_index('data/faiss_db/text/person.faiss')
        elif type == 'subject':
            index = faiss.read_index('data/faiss_db/text/subject.faiss')
        elif type == 'publisher':
            index = faiss.read_index('data/faiss_db/text/publisher.faiss')
        
        query_vector = self.sentence_model.encode([entity], return_tensors=True)
        distances, indices = index.search(query_vector, k)
        print(indices)
        retrieved = list()
        for i,idx in enumerate(indices[0]):
            
            retrieved.append(({'entity':self.df[(self.df.text_id==idx)&(self.df.type==type)].entity.values[0]},{'distance':distances[0][i].item()}))

        return retrieved



'''text = """Find books by authors similar to one written by Achebe"""

template = {
    "QuestionFocus": "",
    "entities": {
        "work": [],
        "person": [],
        "subject":[],
        "publisher":[]
    }
}

retr = Retriever()
res = json.loads(retr.extract_knowledge(template=template, text=text))

print(res)

for item in res['entities']['person']:
    print(retr.link(item,'person'))'''