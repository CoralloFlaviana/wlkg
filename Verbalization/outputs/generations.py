# Installazioni necessarie (da eseguire solo una volta)
# pip install peft transformers trl huggingface_hub accelerate --upgrade torch

import os
import torch
import gc
import pandas as pd
import re
from datasets import Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    pipeline,
)
import ast
from peft import LoraConfig, PeftModel
from huggingface_hub import login

os.environ["CUDA_VISIBLE_DEVICES"] = "0"

# Configurazione gestione memoria PyTorch
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
torch.set_default_dtype(torch.bfloat16 if torch.cuda.is_available() else torch.float32)

# Login HuggingFace
login(token="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")

print(torch.cuda.is_available())
print(torch.cuda.get_device_name(0))

import os

print("Directory corrente:", os.getcwd())


# Paths
data_path_datasets = './unito-projects/talkingraph/dataset'
data_path_models = './unito-projects/talkingraph/models'

models_name = [
    'meta-llama/Llama-3.1-8B-Instruct',
    'mistralai/Mistral-Nemo-Instruct-2407',
    'Qwen/Qwen2.5-7B-Instruct',
]

# LoRA parameters
peft_config = LoraConfig(
    lora_alpha=16,
    lora_dropout=0.1,
    r=64,
    bias="none",
    task_type="CAUSAL_LM",
)

print("Inizializzazione completata")

def prepare_dataset(split):
    print(f"Preparing {data_path_datasets}/{split}.csv dataset...")
    df = pd.read_csv(f'{data_path_datasets}/{split}.csv')
    
    dataset = []
    for index, row in df.iterrows():
        i = 0
        triples_ast = ast.literal_eval(row['subtriples'])
        for triple in triples_ast:
            dataset.append({
                'instruction': f'Given the following triples in (TRIPLE), you have to generate the corresponding text in (ANW)',
                'id': f"{row['id']}-{i}",
                'key': row['key'],
                'input': triple,
                'output': '',
            })
            i += 1

    return Dataset.from_pandas(pd.DataFrame(dataset))

def load_fine_tuned_model(model_name, fine_tuned_model_path):
    base_model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.bfloat16,
        device_map={"": 0}   # Anche qui forzato su cuda:0
    )
    model = PeftModel.from_pretrained(base_model, fine_tuned_model_path)
    model = model.merge_and_unload()

    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    return model, tokenizer

def clear_output(output):
    match = re.search(r'\[ANW\](.*?)\[/ANW\]', output, re.DOTALL)
    return match.group(1).strip() if match else "Output not found"

def model_generation(pipe, test_dataset, output_path):
    records = []
    with torch.no_grad():
        for i, record in enumerate(test_dataset, 1):
            print(f'record #{i}')
            result = pipe(f"<s> [INST] {record['instruction']} [/INST] [TRIPLE] {record['input']} [/TRIPLE] [ANW]")
            prediction = clear_output(result[0]['generated_text'])
            print(f"triples: {record['input']}")
            print(f'prediction: {prediction}')
            print('\n')

            records.append((record['id'], record['input'], prediction, result[0]['generated_text']))

            if i % 5 == 0:
                gc.collect()
                torch.cuda.empty_cache()

            df = pd.DataFrame(records, columns=['id', 'input', 'prediction', 'generation'])
            df.to_csv(output_path, index=False)

# Caricamento dataset
test_dataset = prepare_dataset('test')
print(test_dataset)

print("Dataset caricato correttamente")

print("Inizio generazione")
for model_name in models_name:
    print(f"Generazione {model_name}...")
    clean_model_name = model_name.split('/')[1]
    output_path = f'{data_path_models}/fine-tuned-{clean_model_name}-en'
    print(output_path)

    fine_tuned_model, fine_tuned_tokenizer = load_fine_tuned_model(model_name, f'{output_path}')

    pipe = pipeline(
        'text-generation',
        model=fine_tuned_model,
        tokenizer=fine_tuned_tokenizer,
        max_length=200,
        temperature=0.5,
        eos_token_id=fine_tuned_tokenizer.eos_token_id,
        torch_dtype=torch.bfloat16
    )

    for i in range(1):
        model_generation(pipe, test_dataset, f'{output_path}-decoding-{i+1}.csv')

    print(f"Generazione completata per {model_name}")

    del fine_tuned_model, fine_tuned_tokenizer, pipe
    gc.collect()
    torch.cuda.empty_cache()