"""Bounded search subprocess with independent fallback engines."""
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from urllib.parse import urlparse, quote
from ddgs import DDGS

query = sys.stdin.read(2000).strip()
sources = []
# Dated headline feeds give more useful evidence than generic news homepages.
if re.search(r'\b(news|headlines)\b', query, re.I):
    topic = re.sub(r'(?i)\b(what|are|is|the|latest|headlines|news|today|of|day|give|dates|and|sources|in)\b', ' ', query)
    topic = re.sub(r'[^\w\s-]', ' ', topic).strip() or 'India'
    url = 'https://news.google.com/rss/search?q=' + quote(topic + ' when:1d') + '&hl=en-IN&gl=IN&ceid=IN:en'
    try:
        with urllib.request.urlopen(url, timeout=6) as response: root = ET.fromstring(response.read(1000000))
        for item in root.findall('./channel/item')[:5]:
            sources.append({'title':item.findtext('title','')[:250], 'url':item.findtext('link',''), 'snippet':item.findtext('pubDate','') + ' — ' + item.findtext('title','')})
    except Exception: pass
if not sources:
    for engines in ('duckduckgo,brave', 'yahoo,mojeek,yandex'):
        try:
            results = DDGS(timeout=5).text(query, backend=engines, max_results=5)
            for row in results:
                url = row.get('href', '')
                if urlparse(url).scheme not in ('http', 'https'): continue
                sources.append({'title':row.get('title', '')[:200], 'url':url[:2000], 'snippet':row.get('body', '')[:1000]})
            if sources: break
        except Exception: continue
print(json.dumps(sources[:5]))
