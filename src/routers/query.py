import requests
from fastapi import FastAPI, HTTPException, Query, APIRouter
from SPARQLWrapper import SPARQLWrapper, JSON
import yaml
import os,json
from internal.schemas import SearchResponse, FindResult, SearchResultURI
from internal.config import config as config 
from scripts.retrieval import Retriever
from scripts.query_construction import finder, searchExactly, searchRegex, searchTypeEntity, rel, explorationRel, finder_tmp, typeEntity, getImage, getUrlGoodreads, getUrlOlid, getUrldata

#retriever = Retriever()


query = APIRouter(
    prefix="/query",
    tags=["query"],
    responses={404: {"description": "Not found"}},
)


# Configura endpoint 
SPARQL_ENDPOINT = config.endpoint


@query.get("/search_exactly", response_model=SearchResponse)
def serch_exactly(label: str, property: str=None) -> SearchResponse:
    sparql = SPARQLWrapper(SPARQL_ENDPOINT)
    
    '''entity_key = f"entità{property}"  # Nome chiave da cercare
    
    # Controllo se esiste l'entità richiesta
    if entity_key not in config.namespace.entities_type:
        raise HTTPException(status_code=400, detail=f"Entity {entity_key} not found in config")

    configEntity = config.namespace.entities_type[entity_key].rel  

    # Controllo se il prefisso urw è disponibile
    urw_prefix = config.prefix["urw"]
    if not urw_prefix:
        raise HTTPException(status_code=500, detail="Prefix is missing in configuration")'''

    query = searchExactly(label,property)

    
    try:
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SPARQL Query Error: {str(e)}")

    return {"results": results["results"]["bindings"]}
    


from typing import Optional



    

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

    # Controllo se il prefisso urw è disponibile
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
    #print("Bindings:", bindings)  # Debug: stampa i binding ottenuti
    
    for item in bindings:
        
        #print(f"[search_regex] ENTERED LOOP - Item keys: {item.keys()}")
        result_type = type_label
        #print(f"[search_regex] Processing item: {item} with initial type '{result_type}'")
        
        # Se entity_label era None, provo a estrarre il tipo dall'URL
        if entity_label is None :
            entity_url = item["s"].get("value", "")
            result_type = "altro"  # Default

            #print(f"[search_regex] Trying to determine type for entity URL: {entity_url}")

            result_type = query=typeEntity(entity_url)

            try:
                sparql.setQuery(query)
                sparql.setReturnFormat(JSON)
                results = sparql.query().convert()
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"SPARQL Query Error: {str(e)}")

            if not results["results"]["bindings"]:
                #print(f"[search_regex] No type found for entity URL: {entity_url}, defaulting to 'altro'")
                result_type = "altro"
            else: 
                #print({results["results"]["bindings"][0]["type"]["value"]})
                #type_value = results["results"]["bindings"][1]["type"]["value"] 
                type_value = results["results"]["bindings"][0]["type"]["value"]
                print(f"[search_regex] Found type URI: {type_value}")
                result_type = uri_to_label(type_value)
        
        formatted_results.append({
            **item,
            "type": result_type
        })

    return {"results": formatted_results}



@query.get("/rel")
def relTemp(ris: str) :
    sparql = SPARQLWrapper(SPARQL_ENDPOINT)
    
    # Controllo se il prefisso urw è disponibile
    urw_prefix = config.prefix["urw"]
    if not urw_prefix:
        raise HTTPException(status_code=500, detail="Prefix is missing in configuration")
     
    ris="<"+ris+">"
    #print(ris)
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
        "relazione": item.get("relazione") or rel_to_label(str(item["rel"].get("value"))),
        "rel": item["rel"]
    }
    for item in bindings
]

    #print(formatted_results)

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
    
    #print("Bindings:", formatted_results)  # Debug: stampa i binding ottenuti

    for item in bindings:
        s_value = item["s"]
        sogg_raw = item.get("sogg")

        #print(f"[entityFind] Processing item: {item} with raw sogg: {sogg_raw}")

        sogg_text = sogg_raw.get("value") if isinstance(sogg_raw, dict) else sogg_raw
        sogg_value = sogg_text or rel_to_label(str(s_value.get("value")))


      
        try:
            if s_value["value"]:
                entity_result = type_entity(s_value["value"])
                print(entity_result)

                entity_type = "altro"

                if isinstance(entity_result, dict):
                    results_list = entity_result.get("results", [])

                    for raw_type in results_list:
                        uri_value = raw_type.get("type", {}).get("value") or raw_type.get("value")

                        if uri_value:
                            label = uri_to_label(uri_value)

                            if label != "altro":
                                entity_type = label
                                break
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
        
    #print(formatted_results)
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

    return {"results": results["results"]["bindings"]}



@query.get("/getUrlWikidataFromEntity") #todo_ cambiare nome 
def getUrlWikidataFromEntity(entity: str, rel:str) :
    sparql = SPARQLWrapper(SPARQL_ENDPOINT)
    
    query=getUrldata(entity, rel)

    try:
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SPARQL Query Error: {str(e)}")

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
    
    print(f"[uri_to_label] Received URI: {uri}")

    uri = rel_to_label(uri)  # Pulisce l'URI
    
    try:
        entities_type = config.namespace.entities_type  # Dict[str, Entity]
        for ent_key, ent_data in entities_type.items():
            ns_url = getattr(ent_data, "type", "")
            ns_url = ns_url.split(":", 1)[-1].lower()
            ns_url = ns_url.strip("<>") #rimuove <> eventuali
            #uri = uri.split(":", 1)[-1].lower()  # Prende solo la parte dopo ':'  
            uri = uri.split(":", 0)[-1].lower() 
            label = getattr(ent_data, "label", "")
            print(f"[uri_to_label] Comparing URI '{uri}' with namespace URL '{ns_url}' for label '{label}'")
            print(f"[uri_to_label] Checking against namespace '{ns_url}' with label '{label}'")
            
            if ns_url and (uri == ns_url):
                print(f"[uri_to_label] Matched URI '{uri}' to label '{label}' using namespace '{ns_url}'")
                return label

    except Exception as e:
        print(f"[uri_to_label] Warning: unable to access config namespaces ({e})")
        return "altro"

    return "altro"


"""
FUNZIONE UTILE: Per avere label rel senza label 
"""
def rel_to_label(rel: str) -> str:
    
    rel = rel.strip("<>").lower()  # rimuove eventuali < >
    if "#" in rel:
        rel = rel.split("#", 1)[1]  # prende solo la parte dopo '#'
    else:
        rel = rel.rsplit("/", 1)[-1]  # prende solo la parte dopo l'ultimo '/'

    print(f"[rel_to_label] Processing rel: {rel}")
    
    return rel