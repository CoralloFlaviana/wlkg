import requests

url = 'http://0.0.0.0:8000/query/search_exactly'
params = {
    'label': '1984',
}

req = requests.get(url, params=params)

print(req.json())

