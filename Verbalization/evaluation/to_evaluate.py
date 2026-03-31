import pandas as pd
import random

# File di input
filenames = [
    'fine-tuned-Llama-3.1-8B-Instruct-en-decoding-1.csv',
    'fine-tuned-Mistral-Nemo-Instruct-2407-en-decoding-1.csv',
    'fine-tuned-Qwen2.5-7B-Instruct-en-decoding-1.csv'
]

# Leggi il primo file per selezionare casualmente 50 ID
df_base = pd.read_csv(filenames[0])
all_ids = df_base['id'].unique()
selected_ids = random.sample(list(all_ids), 50)

# Estrai e salva i 50 esempi da ciascun file
for file in filenames:
    df = pd.read_csv(file)
    filtered = df[df['id'].isin(selected_ids)][['id', 'input', 'prediction']]
    output_name = f"toevaluate_50_{file}"
    filtered.to_csv(output_name, index=False)
    print(f"Salvato: {output_name}")