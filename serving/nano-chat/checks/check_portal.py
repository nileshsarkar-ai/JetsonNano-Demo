"""Bounded functional/load check; uses at most 12 concurrent requests."""
import base64, concurrent.futures, json, time, urllib.request, urllib.error
from pathlib import Path
URL='https://d117f15149291.notebooksn.jarvislabs.net'
def call(path='/', body=None, headers=None):
    start=time.monotonic()
    data=None if body is None else json.dumps(body).encode()
    req=urllib.request.Request(URL+path,data=data,headers={'Content-Type':'application/json',**(headers or {})})
    try:
        with urllib.request.urlopen(req,timeout=150) as r: status=r.status; raw=r.read()
    except urllib.error.HTTPError as e: status=e.code;raw=e.read()
    except Exception as e:return {'status':0,'seconds':round(time.monotonic()-start,2),'error':type(e).__name__}
    try: result=json.loads(raw)
    except Exception: result={'page':b'Jetson Nano Demo' in raw}
    return {'status':status,'seconds':round(time.monotonic()-start,2),'result':result}
def batch(name,jobs):
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool: rows=list(pool.map(lambda a:call(*a),jobs))
    results[name]=rows;print(name,json.dumps(rows,ensure_ascii=False),flush=True)
results={}
batch('invalid', [('/chat',[]),('/chat',{'messages':[None]}),('/vision',{'image':'bad'}),('/chat',{'messages':'bad'}),('/chat',{'messages':[]},{'Origin':'https://example.invalid'}),('/missing',None)])
batch('burst', [('/chat',{'messages':[{'role':'user','content':'Reply with the word Ready only.'}]}) for _ in range(8)]+[('/',None) for _ in range(4)])
batch('recovery',[('/chat',{'messages':[{'role':'user','content':'Reply in Hindi with one short greeting.'}]}),('/chat',{'messages':[{'role':'user','content':'Reply in Kannada with one short greeting.'}]})])
frame='data:image/jpeg;base64,'+base64.b64encode(Path('docs/media/nano-product.jpeg').read_bytes()).decode()
batch('features',[('/vision',{'image':frame,'prompt':'List visible objects, labels only.'}),('/chat',{'web':True,'messages':[{'role':'user','content':'Latest NVIDIA news, one sentence with a source.'}]})])
Path('/tmp/nano-portal-check.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
assert [r['status'] for r in results['invalid']] == [400,400,400,400,403,404], 'Invalid input handling failed'
assert all(r['status'] in (200,429) for r in results['burst']), 'Burst had unexpected failures'
assert all(r['status']==200 for r in results['burst'][-4:]), 'Page unavailable under load'
assert any(r['status']==200 for r in results['burst'][:8]), 'No chat completed under load'
assert any(r['status']==429 for r in results['burst'][:8]), 'Overload not exercised'
assert all(r['status']==200 and r['result'].get('answer') for r in results['recovery']+results['features']), 'Recovery or feature failed'
assert results['features'][1]['result'].get('sources'), 'Web sources missing'
print('All bounded checks passed',flush=True)
