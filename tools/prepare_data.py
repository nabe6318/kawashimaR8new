"""筆ポリゴンGeoJSONと調査CSV(Googleスプレッドシートの書き出し)を、Web表示用に軽量化・整形する。

使い方:  python tools/prepare_data.py 筆ポリゴン.geojson 調査結果.csv
出力:    data/fields.geojson, data/survey.csv
(Python標準ライブラリのみで動きます)
"""
import csv, json, sys, os, re

KEEP_PROPS = ["fid", "land_type"]          # 表示に使う属性だけ残す
LAND = {100: "田", 200: "畑"}               # 筆ポリゴンの land_type
SURVEY_COLS = ["fid", "調査日", "作付状況", "作目", "調査者", "備考", "タイムスタンプ"]

def rnd(c):
    return [rnd(x) for x in c] if isinstance(c[0], list) else [round(c[0], 7), round(c[1], 7)]

def main(geo_in, csv_in, out="data"):
    os.makedirs(out, exist_ok=True)
    g = json.load(open(geo_in, encoding="utf-8"))
    feats = []
    for f in g["features"]:
        p = f["properties"]
        props = {k: p.get(k) for k in KEEP_PROPS}
        props["地目"] = LAND.get(p.get("land_type"), "")
        del props["land_type"]
        feats.append({"type": "Feature", "properties": props,
                      "geometry": {"type": f["geometry"]["type"], "coordinates": rnd(f["geometry"]["coordinates"])}})
    with open(f"{out}/fields.geojson", "w", encoding="utf-8") as fo:
        json.dump({"type": "FeatureCollection", "features": feats}, fo, ensure_ascii=False, separators=(",", ":"))

    rows = list(csv.DictReader(open(csv_in, encoding="utf-8-sig")))
    with open(f"{out}/survey.csv", "w", encoding="utf-8", newline="") as fo:
        w = csv.DictWriter(fo, fieldnames=SURVEY_COLS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            if not (r.get("fid") or "").strip():
                continue
            r["fid"] = str(int(float(r["fid"])))
            # タイムスタンプを 2026-06-21 02:57:31 形式にそろえる(並べ替え用)
            n = re.findall(r"\d+", r.get("タイムスタンプ") or "")
            if len(n) >= 6:
                r["タイムスタンプ"] = "%s-%02d-%02d %02d:%02d:%02d" % (n[0], *map(int, n[1:6]))
            w.writerow({k: (r.get(k) or "").strip() for k in SURVEY_COLS})
    print(f"ポリゴン {len(feats)} 筆 → {out}/fields.geojson ({os.path.getsize(out + '/fields.geojson')//1024} KB)")
    print(f"調査記録 {len(rows)} 件 → {out}/survey.csv")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
