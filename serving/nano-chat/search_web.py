"""Bounded search subprocess. Only queries are passed to search providers."""
import json
import sys
from urllib.parse import urlparse
from ddgs import DDGS

query = sys.stdin.read(2000).strip()
results = DDGS(timeout=8).text(query, backend='duckduckgo,brave', max_results=5)
sources = []
for row in results:
    url = row.get('href', '')
    if urlparse(url).scheme not in ('http', 'https'): continue
    sources.append({'title':row.get('title', '')[:200], 'url':url[:2000], 'snippet':row.get('body', '')[:1000]})
print(json.dumps(sources[:5]))
