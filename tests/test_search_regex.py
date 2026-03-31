import requests

url = 'http://0.0.0.0:8000/query/search_regex'
params = {
    'label': 'palla',
}

req = requests.get(url, params=params)

print(req.json())

