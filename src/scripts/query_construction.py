import requests
from fastapi import FastAPI, HTTPException, Query, APIRouter
from SPARQLWrapper import SPARQLWrapper, JSON
import yaml
import os,json
from internal.schemas import SearchResponse, FindResult, SearchResultURI
from internal.config import config as config 


# Configura endpoint 
SPARQL_ENDPOINT = config.endpoint


def searchExactly(label: str, property:str=None ) :
    
    # Costruzione della query SPARQL 
    if property is None:
      query = f"""
      {config.prefixes}
      
      SELECT DISTINCT ?name ?s WHERE {{
      ?s a {configEntity}; 
        
      ''' {{ ?s ?p ?o }} UNION {{ ?o ?p ?s }} .
        ?s {config.search} ?name'''
        
        FILTER((?name = "{label}"))
      }}
      """
    else:
        query = f"""
      {config.prefixes}
      
      SELECT DISTINCT ?name ?titolo WHERE {{
        ?author {configEntity} ?books.
        ?books {config.search} ?titolo.
        ?author {config.search} ?name.
        
        FILTER((?titolo = "{label}") || (?name = "{label}"))
      }}
      """
    print(query)
    return query
    

def searchRegex(label: str, property:str=None ) :
    
    # Costruzione della query SPARQL
    if property is None:
      query = f"""
      {config.prefixes}
      
      SELECT DISTINCT ?name ?s  WHERE {{
        {{ ?s ?p ?o }} UNION {{ ?o ?p ?s }} .
        ?s {config.search} ?name.
          FILTER(regex(?name, "{label}", "i"))

      }}
      GROUP BY ?s ?name
      LIMIT 50
      """
    else:
      query = f"""
      {config.prefixes}
      
      SELECT DISTINCT ?name ?s WHERE {{
        ?s a {configEntity}.
        ?s {config.search} ?name.
        
        FILTER(regex(?name, "{label}", "i"))
      }}
      GROUP BY ?s ?name
       LIMIT 50
      """
    print(query)
    return query


def finder(urw_prefix:str, configEntity:str, o:str):

    # Costruzione della query SPARQL con validazione
    query = f"""
    {config.prefixes}
    
    SELECT DISTINCT ?s ?sogg WHERE {{
      ?s {configEntity} {o}.
      ?s {config.search} ?sogg.
      
    }}
    """
    print(query)
    return query

def searchTypeEntity(urw_prefix:str, entity_type:str) :

 # Costruzione della query SPARQL con validazione
    query = f"""
    {config.prefixes}

    SELECT DISTINCT ?s ?name WHERE {{
      ?s  rdf:type {entity_type}.
      ?s {config.search} ?name.
    }}

    """
    print(query)
    return query

#NOTE: trova le relazioni tra due entità
def rel(urw_prefix:str, ris:str) :
    if (config.arrow == "no"):
      query = f"""
      {config.prefixes}
  
      
      SELECT DISTINCT ?relazione ?rel WHERE {{
          {{
              {ris} ?rel ?o.
              OPTIONAL {{ ?rel {config.search} ?relazione. }}
          }}
          UNION
          {{
              ?o ?rel {ris}.
              OPTIONAL {{ ?rel {config.search} ?relazione. }}
          }}
      }}

      """
    else:
      query = f"""
      {config.prefixes}
  
      
      SELECT DISTINCT ?relazione ?rel WHERE {{
          {{
              {ris} ?rel ?o.
              OPTIONAL {{ ?rel {config.search} ?relazione. }}
          }}
          
      }}

      """
    print(query)
    return query

# NOTE: LATO FRONTEND serve per trovare l'entità legata da una relazione a o (entità visitata al momento)
def explorationRel(urw_prefix:str, configEntity:str, o:str):
  if (config.arrow == "no"):
    # Costruzione della query SPARQL con validazione
    query = f"""
    {config.prefixes}
    
    SELECT DISTINCT ?s ?sogg WHERE {{
    {{
      ?s {configEntity} {o}.
      OPTIONAL {{?s {config.search} ?sogg.}}
    }}UNION{{
      {o} {configEntity} ?s.
      OPTIONAL {{?s {config.search} ?sogg.}}
    }}
      

    }}

    limit 50
    """
  else:
    # Costruzione della query SPARQL con validazione
    query = f"""
    {config.prefixes}

    SELECT DISTINCT ?s ?sogg WHERE {{
    
      {o} {configEntity} ?s.
      OPTIONAL {{?s {config.search} ?sogg.}}
    }}
    limit 50
    """
    
  print(query)
  return query


def finder_tmp(o:str,prop:str=None):

    # Costruzione della query SPARQL con validazione
    if prop is None:
      query = f"""
      {config.prefixes}
      
      SELECT DISTINCT ?sogg ?p WHERE {{
      BIND ({o} as ?o) .
        {{ ?s ?p ?o }} UNION {{ ?o ?p ?s }} .
        ?s {config.search} ?sogg.
        
      }}
      """
    else:
      query = f"""
      {config.prefixes}
      
      SELECT DISTINCT ?sogg ?p WHERE {{
      BIND ({o} as ?o) .
        {{ ?s {prop} ?o}} UNION {{ ?o {prop} ?s }} .
        ?s {config.search} ?sogg.
        
      }}
      """
    print(query)
    return query

#NOTE: return type of entity
def typeEntity(entity:str) :

 # Costruzione della query SPARQL con validazione
    query = f"""
    {config.prefixes}

    SELECT DISTINCT ?type WHERE {{
      <{entity}>  rdf:type ?type.
    }}

    """
    print(query)
    return query

#NOTE: 
def getImage(entity:str):

    # Costruzione della query SPARQL con validazione
    query = f"""
    {config.prefixes} 
    
    SELECT DISTINCT ?img WHERE {{
      <{entity}> foaf:image ?img.   
      
    }}
    """
    print(query)
    return query


#NOTE: LASCIARE
def getUrldata(entity:str, rel:str):

    # Costruzione della query SPARQL con validazione
    query = f"""
    {config.prefixes}
    
    SELECT DISTINCT ?id WHERE {{
      <{entity}> {rel} ?id.
      
    }}
    """
    print(query)
    return query

#NOTE: CANCELLARE
def getUrlGoodreads(entity:str):

    # Costruzione della query SPARQL con validazione
    query = f"""
    {config.prefixes}
    
    SELECT DISTINCT ?gdr WHERE {{
      <{entity}> urw:goodreads ?gdr.
      
    }}
    """
    print(query)
    return query


#NOTE: CANCELLARE
def getUrlOlid(entity:str):

    # Costruzione della query SPARQL con validazione
    query = f"""
    {config.prefixes}
    
    SELECT DISTINCT ?olid WHERE {{
      <{entity}> urw:olid ?olid.
      
    }}
    """
    print(query)
    return query

