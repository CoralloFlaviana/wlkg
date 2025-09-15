import requests
from fastapi import FastAPI, HTTPException, Query, APIRouter
from SPARQLWrapper import SPARQLWrapper, JSON
import yaml
import os,json
from internal.schemas import SearchResponse, FindResult, SearchResultURI
from internal.config import config as config 


# Configura endpoint 
SPARQL_ENDPOINT = config.endpoint


def searchExactly(label: str, urw_prefix:str, configEntity:str=None ) :
    
    # Costruzione della query SPARQL 
    if configEntity is None:
      query = f"""
      {config.prefixes}
      
      SELECT DISTINCT ?name ?titolo WHERE {{
        ?author ?rel ?books.
        ?books rdfs:label ?titolo.
        ?author rdfs:label ?name.
        
        FILTER((?titolo = "{label}") || (?name = "{label}"))
      }}
      """
    else:
        query = f"""
      {config.prefixes}
      
      SELECT DISTINCT ?name ?titolo WHERE {{
        ?author {configEntity} ?books.
        ?books rdfs:label ?titolo.
        ?author rdfs:label ?name.
        
        FILTER((?titolo = "{label}") || (?name = "{label}"))
      }}
      """
    print(query)
    return query
    

def searchRegex(label: str, urw_prefix:str, configEntity:str=None ) :
    
    # Costruzione della query SPARQL
    if configEntity is None:
      query = f"""
      {config.prefixes}
      
      SELECT DISTINCT ?name ?titolo WHERE {{
        ?author ?rel ?books.
        ?books rdfs:label ?titolo.
        ?author rdfs:label ?name.
        
          FILTER(regex(?titolo, "{label}", "i") || regex(?name, "{label}", "i"))

      }}
      """
    else:
      query = f"""
      {config.prefixes}
      
      SELECT DISTINCT ?name ?titolo WHERE {{
        ?author {configEntity} ?books.
        ?books rdfs:label ?titolo.
        ?author rdfs:label ?name.
        
        FILTER(regex(?titolo, "{label}", "i") || regex(?name, "{label}", "i"))
      }}
      """
      print(query)
    return query


def finder(urw_prefix:str, configEntity:str, o:str):

    # Costruzione della query SPARQL con validazione
    query = f"""
    {config.prefixes}
    
    SELECT DISTINCT ?s, ?sogg WHERE {{
      ?s {configEntity} {o}.
      ?s rdfs:label ?sogg.
      
    }}
    """
    print(query)
    return query

def searchTypeEntity(urw_prefix:str, entity_type:str) :

 # Costruzione della query SPARQL con validazione
    query = f"""
    {config.prefixes}

    SELECT DISTINCT ?s, ?name WHERE {{
      ?s  rdf:type {entity_type}.
      ?s rdfs:label ?name.
    }}

    """
    print(query)
    return query

#NOTE: trova le relazioni tra due entità
def rel(urw_prefix:str, ris:str) :
    query = f"""
    {config.prefixes}
 
    SELECT DISTINCT ?relazione ?rel WHERE {{
     {{
       {ris} ?rel ?o.  
      ?rel rdfs:label ?relazione.
      }}
    UNION {{
       ?o ?rel {ris}.
      ?rel rdfs:label ?relazione. 
      }}
    }}

    """
    print(query)
    return query

# NOTE: LATO FRONTEND serve per trovare l'entità legata da una relazione a o (entità visitata al momento)
def explorationRel(urw_prefix:str, configEntity:str, o:str):

    # Costruzione della query SPARQL con validazione
    query = f"""
    {config.prefixes}
    
    SELECT DISTINCT ?s, ?sogg WHERE {{
    {{
      ?s {configEntity} {o}.
      ?s rdfs:label ?sogg.
    }}UNION{{
      {o} {configEntity} ?s.
      ?s rdfs:label ?sogg.
    }}
      
      
    }}
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
        ?s rdfs:label ?sogg.
        
      }}
      """
    else:
      query = f"""
      {config.prefixes}
      
      SELECT DISTINCT ?sogg ?p WHERE {{
      BIND ({o} as ?o) .
        {{ ?s {prop} ?o}} UNION {{ ?o {prop} ?s }} .
        ?s rdfs:label ?sogg.
        
      }}
      """
    print(query)
    return query