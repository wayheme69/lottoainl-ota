#!/usr/bin/env python3
"""Robot LOTTO AI NL — tirages officiels de la Nederlandse Loterij (Lotto + Lotto XL).
Source : API officielle lotto-api.nederlandseloterij.nl (accessible depuis GitHub Actions).
Écrit nl_results.json (30 derniers tirages + prochain tirage) et complète history.json (tous les tirages depuis 2010)."""
import json, time, urllib.request
API = "https://lotto-api.nederlandseloterij.nl/api"
UA = {"User-Agent": "Mozilla/5.0 (LOTTO AI NL results robot)", "Accept": "application/json"}

def get(path):
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(API + path, headers=UA), timeout=30) as r:
                return json.load(r)
        except Exception as e:
            if attempt == 3: raise
            time.sleep(5 * (attempt + 1))

def valid(nums, bonus):
    return (len(nums) == 6 and len(set(nums)) == 6 and all(1 <= n <= 45 for n in nums)
            and len(bonus) == 1 and 1 <= bonus[0] <= 45 and bonus[0] not in nums)

def draws_of(date):
    """Un samedi normal : Lotto + XL. Super Zaterdag : Lotto 1, XL 1, Lotto 2, XL 2."""
    res = get(f"/draws/results/{date}").get("results", [])
    lotto = [r for r in res if not r.get("isXlDraw")]
    xl = [r for r in res if r.get("isXlDraw")]
    sz = len(lotto) > 1
    out = []
    for i, r in enumerate(lotto):
        w = r["winningNumbers"]; nums = sorted(w["numbers"]); bonus = [w["bonusNumber"]]
        if not valid(nums, bonus): continue
        d = {"date": date, "draw": i + 1, "superZaterdag": sz, "numbers": nums, "bonus": bonus,
             "jackpot": (r.get("jackpotAmountGross") or 0) / 100 or None, "jackpotWon": bool(r.get("isJackpotWon"))}
        if i < len(xl):
            xw = xl[i]["winningNumbers"]; xn = sorted(xw["numbers"]); xb = [xw["bonusNumber"]]
            if valid(xn, xb): d["xl"] = {"numbers": xn, "bonus": xb}
        out.append(d)
    return out

def main():
    dates = sorted({d["drawDate"] for d in get("/draws/published").get("publishedDraws", [])}, reverse=True)
    recent = []
    for date in dates:
        recent += sorted(draws_of(date), key=lambda d: -d["draw"])
        if len(recent) >= 30: break
        time.sleep(1)
    assert recent, "aucun tirage"
    info = get("/settings/game-information")
    nxt = {"date": info["drawDate"][:10], "salesClose": info.get("drawSalesCloseDateTime"),
           "estimatedPrize": (info.get("jackpotAmount") or 0) / 100 or None}
    json.dump({"source": "Nederlandse Loterij (official API)", "updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "lotto": recent[:30], "next": nxt}, open("nl_results.json", "w"), ensure_ascii=False, indent=1)
    # Historique complet : on ajoute les nouveaux tirages (jamais de réécriture des anciens)
    hist = json.load(open("history.json"))
    have = {(h["date"], h["draw"]) for h in hist}
    new = [{k: d[k] for k in ("date", "draw", "superZaterdag", "numbers", "bonus", "xl") if k in d}
           for d in recent if (d["date"], d["draw"]) not in have]
    if new:
        hist = sorted(hist + new, key=lambda h: (h["date"], h["draw"]))
        json.dump(hist, open("history.json", "w"), ensure_ascii=False, separators=(",", ":"))
    print(f"{len(recent)} tirages récents, dernier {recent[0]['date']} ; {len(new)} ajoutés à l'historique ({len(hist)}) ; prochain {nxt}")

if __name__ == "__main__":
    main()
