import requests

# Search for clarity on Maven
r = requests.get('https://search.maven.org/solrsearch/select?q=clarity&rows=10&wt=json')
print("Status:", r.status_code)
print("Response:", r.text[:2000])