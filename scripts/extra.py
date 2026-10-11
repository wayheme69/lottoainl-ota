# lotterytexts.com: year pages + "load all" AJAX (nonce read from each page)
import urllib.request, urllib.parse, re, time, os, json, gzip
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'
os.makedirs('out', exist_ok=True); st = {}
def get(url, data=None):
    h = {'User-Agent': UA, 'Accept-Encoding': 'gzip'}
    if data: h['Content-Type'] = 'application/x-www-form-urlencoded'; h['X-Requested-With'] = 'XMLHttpRequest'
    r = urllib.request.urlopen(urllib.request.Request(url, data=data, headers=h), timeout=60)
    b = r.read()
    if r.headers.get('Content-Encoding') == 'gzip': b = gzip.decompress(b)
    return r.status, b
for y in range(2017, 2027):
    try:
        c, b = get(f'https://lotterytexts.com/netherlands/lotto/past-results/{y}/')
        open(f'out/lt_{y}.html', 'wb').write(b)
        t = b.decode('utf-8', 'replace')
        m = re.search(r"action: 'past_results_all_ajax', lottery_id: '(\d+)', year: '(\d+)', nonce: '([0-9a-f]+)'", t)
        st[f'lt_{y}'] = [c, len(b), bool(m)]
        time.sleep(2)
        if m:
            d = urllib.parse.urlencode({'action': 'past_results_all_ajax', 'lottery_id': m.group(1), 'year': m.group(2), 'nonce': m.group(3)}).encode()
            c2, b2 = get('https://lotterytexts.com/wp-admin/admin-ajax.php', d)
            open(f'out/lt_{y}_all.html', 'wb').write(b2); st[f'lt_{y}_all'] = [c2, len(b2)]
            time.sleep(2)
    except Exception as e:
        st[f'lt_{y}'] = repr(e)[:200]
    print(y, st.get(f'lt_{y}'), st.get(f'lt_{y}_all'), flush=True)
json.dump(st, open('out/_extra_status.json', 'w'), indent=1)
