import ast
import re
import pandas as pd

file_path = './unito-projects/talkingraph/dataset/output.txt'
records = {}

def is_clean_key(key):
    return bool(key.strip()) and re.match(r'^[\w\s\-:,]+$', key)

# Legge riga per riga il file
with open(file_path, 'r', encoding='utf-8') as f:
    i = 1
    for line in f:
        triple_dict = {}
        try:
            data = ast.literal_eval(line.strip())
            for entry in data:
                for key, triples in entry.items():
                    if is_clean_key(key) and triples:  # <-- aggiunto controllo per valori non vuoti
                        if key not in triple_dict:
                            triple_dict[key] = []
                        triple_dict[key].extend(triples)
        except Exception as e:
            print(f"Errore nella riga: {line.strip()}\n{e}")

        # Rimuovi le chiavi con liste vuote (ulteriore sicurezza)
        triple_dict = {k: v for k, v in triple_dict.items() if v}

        records[i] = triple_dict
        i += 1


# Stampa i risultati
for i, record in records.items():
    print(f"Record {i}:")
    for key, triples in record.items():
        print(f"  {key}: {triples}")
        print(len(triples))
        break
    print('\n')

print(f"\nNumero totale di record: {len(records)}")

# Stampa il numero totale di triple per ogni record
for i, record in records.items():
    total_triples = sum(len(triples) for triples in record.values())
    print(f"Record {i} ha {total_triples} triple.")


data = []

for i, record in records.items():
    for key, triples in record.items():
        print(f"Record {i} - {key}: ({len(triples)}) {triples}")
        buffer = []
        #subtriples = []

        for tripla in triples:
            buffer.append(' '.join(tripla))
            #if len(buffer) == 3:
                #subtriples.append(' '.join(buffer))
                #buffer = []

        #if buffer:
            #subtriples.append(' '.join(buffer))

        # Aggiunge una riga al DataFrame per ogni record (usando solo la prima chiave, come nel tuo codice)
        data.append({'id': i, 'key': key, 'subtriples': buffer})
        break  # Se vuoi considerare solo la prima chiave, come nel codice originale

# Crea il DataFrame
df = pd.DataFrame(data)

# tocsv
df.to_csv('test.csv', index=False)