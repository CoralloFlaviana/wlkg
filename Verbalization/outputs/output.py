import pandas as pd

filenames = ['fine-tuned-Llama-3.1-8B-Instruct-en-decoding-1.csv', 'fine-tuned-Mistral-Nemo-Instruct-2407-en-decoding-1.csv', 'fine-tuned-Qwen2.5-7B-Instruct-en-decoding-1.csv']


for filename in filenames:
    # Leggi il file
    df = pd.read_csv(filename)

    # Estrai la parte prima del '-' come nuovo gruppo_id
    df['group_id'] = df['id'].apply(lambda x: x.split('-')[0])

    # Ordina per group_id e posizione (la parte dopo il '-')
    df['position'] = df['id'].apply(lambda x: int(x.split('-')[1]))
    df.sort_values(by=['group_id', 'position'], inplace=True)

    # Raggruppa per group_id e concatena le prediction in ordine
    grouped = df.groupby('group_id')['prediction'].apply(lambda x: ' '.join(x)).reset_index()

    # Rinomina le colonne finali
    grouped.rename(columns={'group_id': 'id', 'prediction': 'answer'}, inplace=True)

    # Salva il file
    grouped.to_csv(f'output-{filename}', index=False)