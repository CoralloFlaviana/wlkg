import requests
from fastapi import FastAPI, HTTPException, Query, APIRouter
from SPARQLWrapper import SPARQLWrapper, JSON
import yaml
import os,json
from internal.schemas import SearchResponse, FindResult, SearchResultURI
from internal.config import config as config 
from scripts.retrieval import Retriever
from scripts.query_construction import finder, searchExactly, searchRegex, searchTypeEntity, rel, explorationRel, finder_tmp, typeEntity, getImage, getUrlGoodreads, getUrlOlid, getUrlWikidata

retriever = Retriever()


query = APIRouter(
    prefix="/query",
    tags=["query"],
    responses={404: {"description": "Not found"}},
)


# Configura endpoint 
SPARQL_ENDPOINT = config.endpoint


@query.get("/search_exactly", response_model=SearchResponse)
def serch_exactly(label: str, numberEntity: int) -> SearchResponse:
    sparql = SPARQLWrapper(SPARQL_ENDPOINT)
    
    entity_key = f"entità{numberEntity}"  # Nome chiave da cercare
    
    # Controllo se esiste l'entità richiesta
    if entity_key not in config.namespace.entities_type:
        raise HTTPException(status_code=400, detail=f"Entity {entity_key} not found in config")

    configEntity = config.namespace.entities_type[entity_key].rel  

    # Controllo se il prefisso urw è disponibile
    urw_prefix = config.prefix["urw"]
    if not urw_prefix:
        raise HTTPException(status_code=500, detail="Prefix is missing in configuration")

    query = searchExactly(label,urw_prefix, configEntity)

    
    try:
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SPARQL Query Error: {str(e)}")

    return {"results": results["results"]["bindings"]}
    


from typing import Optional

@query.get("/search_regex", response_model=SearchResponse)
def search_regex(
    label: str, 
    entity_label: Optional[str] = Query(None)
) -> SearchResponse:
    sparql = SPARQLWrapper(SPARQL_ENDPOINT)
    
    configEntity = None
    type_label = "altro"

    # Cerco per label 
    if entity_label is not None:
        # Cerco tra tutte le entità in config.namespace.entities_type
        found_entity = None
        for key, entity in config.namespace.entities_type.items():
            if entity.label.lower() == entity_label.lower():
                found_entity = entity
                break

        if not found_entity:
            raise HTTPException(status_code=400, detail=f"Entity label '{entity_label}' not found in config")

        configEntity = found_entity.type
        type_label = found_entity.label

    #Controllo se il prefisso urw è disponibile
    urw_prefix = config.prefix.get("urw")
    if not urw_prefix:
        raise HTTPException(status_code=500, detail="Prefix is missing in configuration")

    # Costruisco la query SPARQL
    query = searchRegex(label, urw_prefix, configEntity)
    
    try:
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SPARQL Query Error: {str(e)}")

    bindings = results["results"]["bindings"]

    formatted_results = []
    for item in bindings:
        formatted_results.append({
            **item,
            "type": type_label
        })

    return {"results": formatted_results}

    

@query.get("/find", response_model=FindResult)
def find(rel: str, o: str) -> FindResult:
    sparql = SPARQLWrapper(SPARQL_ENDPOINT)
    
    # Controllo se il prefisso urw è disponibile
    urw_prefix = config.prefix["urw"]
    if not urw_prefix:
        raise HTTPException(status_code=500, detail="Prefix is missing in configuration")

    
    entity_key = f"entità{rel}"  # Nome chiave da cercare
    
    # Controllo se esiste l'entità richiesta
    if entity_key not in config.namespace.entities_type:
        raise HTTPException(status_code=400, detail=f"Entity {entity_key} not found in config")

    configEntity = config.namespace.entities_type[entity_key].rel  

    query=finder(urw_prefix, configEntity, o)

    try:
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SPARQL Query Error: {str(e)}")

    # Trasforma la risposta per Pydantic
    bindings = results["results"]["bindings"]
    formatted_results = [{"s": item["s"], "sogg": item["sogg"]} for item in bindings]

    return {"results": formatted_results}


@query.get("/search_typeEntity", response_model=SearchResultURI)
def search_type(entitytype: str) -> SearchResultURI:
    sparql = SPARQLWrapper(SPARQL_ENDPOINT)
    
    # Controllo se il prefisso urw è disponibile
    urw_prefix = config.prefix["urw"]
    if not urw_prefix:
        raise HTTPException(status_code=500, detail="Prefix is missing in configuration")

    
    entity_key = f"entità{entitytype}"  # Nome chiave da cercare
    
    # Controllo se esiste l'entità richiesta
    if entity_key not in config.namespace.entities_type:
        raise HTTPException(status_code=400, detail=f"Entity {entity_key} not found in config")

    prefix_type = config.namespace.entities_type[entity_key].prefix
    entity_type = config.namespace.entities_type[entity_key].type  

    query=searchTypeEntity(urw_prefix, entity_type)
    
    try:
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SPARQL Query Error: {str(e)}")

    # Trasforma la risposta per Pydantic
    bindings = results["results"]["bindings"]
    formatted_results = [{"s": item["s"], "name": item["name"]} for item in bindings]

    return {"results": formatted_results}



@query.get("/graphrag")
def retrieve(text:str,type:str,k:int):
    sparql = SPARQLWrapper(SPARQL_ENDPOINT)
    template= eval(config.template)
    my_res = []
    result = retriever.extract_knowledge(template=template,text=text)
    result = json.loads(result)

    for res in result['entities'][type]:

        linked = retriever.link(res,type,k)
        
    
        my_res.extend(linked)

    print(my_res)
    query = finder_tmp(f"urw:{my_res[0][0]['entity']}")
    
    try:
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SPARQL Query Error: {str(e)}")

    # Trasforma la risposta per Pydantic
    bindings = results["results"]["bindings"]
    formatted_results = [{"sogg": item["sogg"], "s": item["p"]} for item in bindings]

    return {"results": formatted_results}


@query.get("/rel")
def relTemp(ris: str) :
    sparql = SPARQLWrapper(SPARQL_ENDPOINT)
    
    # Controllo se il prefisso urw è disponibile
    urw_prefix = config.prefix["urw"]
    if not urw_prefix:
        raise HTTPException(status_code=500, detail="Prefix is missing in configuration")
     
    ris="<"+ris+">"
    print(ris)
    query=rel(urw_prefix, ris)
    
    try:
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SPARQL Query Error: {str(e)}")

    # Trasforma la risposta per Pydantic
    bindings = results["results"]["bindings"]
    formatted_results = [
    {
        "relazione": item.get("relazione"),  # se manca, None
        "rel": item["rel"]
    }
    for item in bindings
]

    print(formatted_results)

    return {"results": formatted_results}


@query.get("/entityFind", response_model=FindResult)
def entityFind(rel: str, o: str) -> FindResult:
    sparql = SPARQLWrapper(SPARQL_ENDPOINT)
    
    urw_prefix = config.prefix["urw"]
    if not urw_prefix:
        raise HTTPException(status_code=500, detail="Prefix is missing in configuration")
    
    rel = f"<{rel}>"
    o = f"<{o}>"

    query = explorationRel(urw_prefix, rel, o)

    try:
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SPARQL Query Error: {str(e)}")

    bindings = results["results"]["bindings"]
    formatted_results = []

    for item in bindings:
        s_value = item["s"]
        sogg_value = item["sogg"]

        try:
            if s_value["value"]:
                entity_result = type_entity(s_value["value"])
                print(entity_result)
                if isinstance(entity_result, dict):
                    results_list = entity_result.get("results", [])
                    if results_list:
                        raw_type = results_list[0]
                        uri_value = raw_type.get("type", {}).get("value") or raw_type.get("value") or "altro"
                        entity_type = uri_to_label(uri_value)
                    else:
                        entity_type = "altro"
                else:
                    entity_type = str(entity_result)
            else:
                entity_type = "altro"
        except Exception as e:
            entity_type = f"Error: {str(e)}"

        formatted_results.append({
            "s": s_value,
            "sogg": sogg_value,
            "type": entity_type  
        })

    print(formatted_results)
    return {"results": formatted_results}



@query.get("/typeEntity")
def type_entity(entity: str) :
    sparql = SPARQLWrapper(SPARQL_ENDPOINT)
    
    query=typeEntity(entity)

    try:
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SPARQL Query Error: {str(e)}")


    return {"results": results["results"]["bindings"]}



@query.get("/getImageFromEntity")
def getImageFromEntity(entity: str) :
    sparql = SPARQLWrapper(SPARQL_ENDPOINT)
    
    query=getImage(entity)

    try:
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SPARQL Query Error: {str(e)}")
#todo: caso in cui non c'è immagine

    return {"results": results["results"]["bindings"]}



@query.get("/getUrlWikidataFromEntity")
def getUrlWikidataFromEntity(entity: str) :
    sparql = SPARQLWrapper(SPARQL_ENDPOINT)
    
    query=getUrlWikidata(entity)

    try:
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SPARQL Query Error: {str(e)}")
#todo: caso in cui non c'è url

    return {"results": results["results"]["bindings"]}



@query.get("/getUrlGoodreadsFromEntity")
def getUrlGoodreadsFromEntity(entity: str) :
    sparql = SPARQLWrapper(SPARQL_ENDPOINT)
    
    query=getUrlGoodreads(entity)

    try:
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SPARQL Query Error: {str(e)}")
#todo: caso in cui non c'è url

    return {"results": results["results"]["bindings"]}


@query.get("/getUrlOlidFromEntity")
def getUrlOlidFromEntity(entity: str) :
    sparql = SPARQLWrapper(SPARQL_ENDPOINT)
    
    query=getUrlOlid(entity)

    try:
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SPARQL Query Error: {str(e)}")
#todo: caso in cui non c'è url

    return {"results": results["results"]["bindings"]}




"""
FUNZIONE UTILE:
    Converte un URI in una label leggibile.
    Se l'URI corrisponde a uno dei namespace definiti in
    config.app.namespace.entities_type, restituisce la label corrispondente.
    Altrimenti restituisce 'altro'.
"""
def uri_to_label(uri: str) -> str:
    if not uri or not isinstance(uri, str):
        return "altro"

    uri = uri.strip("<>").lower()  # rimuove eventuali < >
    if "#" in uri:
        uri = uri.split("#", 1)[1]  # prende solo la parte dopo '#'
    print(f"[uri_to_label] Processing URI: {uri}")
    
    try:
        entities_type = config.namespace.entities_type  # Dict[str, Entity]
        for ent_key, ent_data in entities_type.items():
            ns_url = getattr(ent_data, "label", "")
            label = getattr(ent_data, "label", "")


            if ns_url and (uri == ns_url or uri.startswith(ns_url)):
                print(f"[uri_to_label] Matched URI '{uri}' to label '{label}' using namespace '{ns_url}'")
                return label

    except Exception as e:
        print(f"[uri_to_label] Warning: unable to access config namespaces ({e})")

    return "altro"


