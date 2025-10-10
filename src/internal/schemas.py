#qui metto classi per field e base model per validazione parametri
from pydantic import BaseModel, Field, field_validator
from typing import List, Dict

from pydantic_settings import BaseSettings

class LiteralValue(BaseModel):
    type: str
    value: str

class SearchResult(BaseModel):
    name: LiteralValue
    s: LiteralValue

class SearchResponse(BaseModel):
    results: List[SearchResult]


class FindResultItem(BaseModel):
    s: str
    sogg: str

    @field_validator("s", "sogg", mode="before")
    @classmethod
    def extract_value(cls, v):
        """ Estrae il valore dalla risposta SPARQL """
        if isinstance(v, dict) and "value" in v:
            return v["value"]
        return v

class FindResult(BaseModel):
    results: List[FindResultItem]

class SearchResultItem(BaseModel):
    s: str
    name: str

    @field_validator("s", "name", mode="before")
    @classmethod
    def extract_value(cls, v):
        """ Estrae il valore dalla risposta SPARQL """
        if isinstance(v, dict) and "value" in v:
            return v["value"]
        return v

class SearchResultURI(BaseModel):
    results: List[SearchResultItem]

# Modelli Pydantic per il file YML
class Entity(BaseModel):
    label: str
    rel: str

class EntityType(BaseModel):
    type: str  
    prefix: str

class Namespace(BaseModel):
    left: Dict[str, EntityType]
    right: Dict[str, Entity]

class Config(BaseSettings):
    name: str
    endpoint: str
    namespace: Namespace
    prefix: Dict[str, str]
    template: str
    prefixes: str


# Models for Information Extraction

class Template(BaseModel):
    prompt: str
    template: str