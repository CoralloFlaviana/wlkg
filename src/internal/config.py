from typing import Dict
from pathlib import Path
import yaml
import os
from internal.schemas import Config


# Definisco il percorso del file di configurazione
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CONFIG_PATH = os.path.join(BASE_DIR, "config copy.yml") 

# Funzione per caricare e trasformare i dati YAML in un oggetto Pydantic
def load_yaml_config(filepath: str = CONFIG_PATH) -> Config:
    config_path = Path(filepath)
    print(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {filepath}")

    with config_path.open("r", encoding="utf-8") as file:
        yaml_data = yaml.safe_load(file)

    return Config(**yaml_data["app"])  # Converto il dizionario in un oggetto Pydantic


# Carica la configurazione
config = load_yaml_config()