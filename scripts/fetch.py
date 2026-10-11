# Generic polite fetcher: reads jobs/urls.json [[id,url],...], writes out/<id>, out/_status.json
import json, os, time, urllib.request, urllib.error, gzip, ssl
jobs = json.load(open('jobs/urls.json'))
os.makedirs('out', exist_ok=True)
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'
st = {}
sp = json.load(open('out/_status.json')) if os.path.exists('out/_status.json') else {}
delay = float(os.environ.get('DELAY', '1.5'))
for job in jobs:
    jid, url = job[0], job[1]; post = job[2] if len(job) > 2 else None
    h = {'User-Agent': UA, 'Accept': 'text/html,application/json,*/*', 'Accept-Language': 'nl-NL,nl;q=0.9,en;q=0.8', 'Accept-Encoding': 'gzip'}
    code, body, final, err = None, b'', url, None
    for attempt in range(2):
        try:
            ctx = ssl._create_unverified_context() if attempt else None
            data = post.encode() if post else None
            if data: h['Content-Type'] = 'application/x-www-form-urlencoded'
            r = urllib.request.urlopen(urllib.request.Request(url, data=data, headers=h), timeout=40, context=ctx)
            code, final = r.status, r.geturl(); body = r.read()
            if r.headers.get('Content-Encoding') == 'gzip': body = gzip.decompress(body)
            break
        except urllib.error.HTTPError as e:
            code = e.code; body = e.read() or b''
            try:
                if e.headers.get('Content-Encoding') == 'gzip': body = gzip.decompress(body)
            except Exception: pass
            break
        except Exception as e:
            err = repr(e)[:300]; time.sleep(3)
    open(f'out/{jid}', 'wb').write(body[:4_000_000])
    st[jid] = {'url': url, 'code': code, 'final': final, 'len': len(body), 'err': err}
    print(jid, code, len(body), err, flush=True)
    time.sleep(delay)
sp.update(st)
json.dump(sp, open('out/_status.json', 'w'), indent=1)
