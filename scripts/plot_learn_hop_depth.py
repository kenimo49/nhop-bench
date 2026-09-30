#!/usr/bin/env python3
"""kenimoto.dev /learn/knowledge-graph/ 第3章 (hop-depth-limit) の本文図を results から描く。

  python3 scripts/plot_learn_hop_depth.py --out ~/repos/kenimoto-dev/public/images/learn/knowledge-graph

数字は手で打たない。results/*.json の rows を analyze.py と同じ規則で集計し、
値を埋め込んだ HTML (SVG) を書き出す。PNG 化は kenimoto-dev 側で
  node scripts/render-figure.mjs --size 1600x900 public/images/learn/knowledge-graph/<base>

書き出すもの:
  hop-depth-levels.html  graph 条件の段数別完全一致率 (4b / 9b / 35b-a3b)
  hop-depth-slope.html   2段以上 (n=71) の完全一致 bare → graph (5モデル) と 4b の再現率・適合率
  hop-depth-think.html   35b-a3b の思考なし / 思考あり (2段以上)
"""
import argparse, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LADDER = "results/2026-09-05-qwen3.5-ladder.json"
THINK = "results/2026-09-05-35b-think.json"

NAVY, BLUE, MID, PALE, RED, INK, SUB = "#1E3A5F", "#2E5F9E", "#5B8BC9", "#9FB3C8", "#B4471F", "#0B1B2E", "#3B4F66"

BASE_CSS = """*{margin:0;padding:0;box-sizing:border-box;}
html,body{width:1600px;height:900px;overflow:hidden;background:#F0F4F8;font-family:'Noto Sans CJK JP','Noto Sans JP',sans-serif;color:#0B1B2E;}
.t{position:absolute;left:64px;top:36px;font-size:40px;font-weight:900;}
.t span{color:#2E5F9E;}
.s{position:absolute;left:64px;top:96px;font-size:24px;font-weight:600;color:#3B4F66;}
.foot{position:absolute;left:64px;right:64px;bottom:28px;font-size:22px;font-weight:600;color:#3B4F66;line-height:1.5;}
svg text{font-family:'Noto Sans CJK JP','Noto Sans JP',sans-serif;}
"""


def load(p):
    return json.loads((ROOT / p).read_text())


def pct(rows):
    return 100 * sum(r["exact"] for r in rows) / len(rows)


def mean(rows, k):
    return sum(r[k] for r in rows) / len(rows)


def sel(rows, **kw):
    lo = kw.pop("min_level", None)
    out = [r for r in rows if all(r[k] == v for k, v in kw.items())]
    if lo is not None:
        out = [r for r in out if r["level"] >= lo]
    return out


def header(name, what, cmd_extra=""):
    return (f"<!-- 第3章 hop-depth-limit {what}\n"
            f"     生成: nhop-bench/scripts/plot_learn_hop_depth.py (数値はこのスクリプトが results から集計して埋め込む。手で直さない)\n"
            f"     出典: nhop-bench/{LADDER}{cmd_extra}\n"
            f"     再生成: cd ~/repos/nhop-bench && python3 scripts/plot_learn_hop_depth.py --out ~/repos/kenimoto-dev/public/images/learn/knowledge-graph\n"
            f"             cd ~/repos/kenimoto-dev && node scripts/render-figure.mjs --size 1600x900 public/images/learn/knowledge-graph/{name} -->\n")


# ---------------------------------------------------------------- levels
def levels_fig(d):
    rows = d["rows"]
    n_by = d["sample_by_level"]
    models = [("qwen3.5:9b", "9b", NAVY), ("qwen3.5:35b-a3b", "35b-a3b", MID), ("qwen3.5:4b", "4b", RED)]
    lv = [1, 2, 3, 4]
    val = {m: [round(pct(sel(rows, model=m, condition="graph", level=l))) for l in lv] for m, _, _ in models}
    # 本文 83-89行と一致しているか (一致しなければ図を書かずに止める)
    assert val["qwen3.5:9b"] == [90, 70, 37, 22], val
    assert val["qwen3.5:35b-a3b"] == [90, 50, 13, 11], val
    assert val["qwen3.5:4b"] == [77, 3, 0, 0], val

    X0, X1, Y0, Y1 = 210, 1060, 190, 730  # plot area
    xs = {l: X0 + 90 + (l - 1) * (X1 - X0 - 180) / 3 for l in lv}
    y = lambda v: Y1 - v / 100 * (Y1 - Y0)
    s = []
    # L1 shading
    s.append(f'<rect x="{X0}" y="{Y0-20}" width="{(xs[1]+xs[2])/2-X0:.0f}" height="{Y1-Y0+20}" fill="#E1E7EF"/>')
    for g in (0, 25, 50, 75, 100):
        s.append(f'<line x1="{X0}" x2="{X1}" y1="{y(g):.0f}" y2="{y(g):.0f}" stroke="#D3DCE7" stroke-width="2"/>')
        s.append(f'<text x="{X0-16}" y="{y(g)+9:.0f}" text-anchor="end" font-size="26" fill="{SUB}" font-weight="600">{g}%</text>')
    s.append(f'<line x1="{X0}" x2="{X1}" y1="{Y1}" y2="{Y1}" stroke="{SUB}" stroke-width="3"/>')
    for l in lv:
        s.append(f'<text x="{xs[l]:.0f}" y="{Y1+40}" text-anchor="middle" font-size="28" font-weight="800" fill="{INK}">{l}段</text>')
        note = f'{n_by[str(l)]}問' + (' (参考値)' if l == 4 else '')
        s.append(f'<text x="{xs[l]:.0f}" y="{Y1+74}" text-anchor="middle" font-size="23" font-weight="600" fill="{SUB}">{note}</text>')
    cx1 = (X0 + (xs[1] + xs[2]) / 2) / 2
    s.append(f'<text x="{cx1:.0f}" y="{Y1-70}" text-anchor="middle" font-size="23" font-weight="700" fill="{SUB}">答えを写すだけ</text>')
    s.append(f'<text x="{cx1:.0f}" y="{Y1-40}" text-anchor="middle" font-size="23" font-weight="700" fill="{SUB}">(比較しない)</text>')
    for m, lab, col in models:
        v = val[m]
        pts = " ".join(f"{xs[l]:.0f},{y(v[i]):.0f}" for i, l in enumerate(lv) if l >= 2)
        s.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="6" stroke-linejoin="round"/>')
        for i, l in enumerate(lv):
            filled = col if l >= 2 else "#F0F4F8"
            s.append(f'<circle cx="{xs[l]:.0f}" cy="{y(v[i]):.0f}" r="10" fill="{filled}" stroke="{col}" stroke-width="5"/>')
    # 値ラベル。重なりを避けるため位置を個別に決める (値は val から)
    def lab(x, yy, text, col, anchor="middle"):
        s.append(f'<text x="{x:.0f}" y="{yy:.0f}" text-anchor="{anchor}" font-size="27" font-weight="900" fill="{col}">{text}</text>')
    v9, v35, v4 = val["qwen3.5:9b"], val["qwen3.5:35b-a3b"], val["qwen3.5:4b"]
    assert v9[0] == v35[0]
    lab(xs[1], y(v9[0]) - 22, f"9b・35b-a3b {v9[0]}%", NAVY)
    lab(xs[1], y(v4[0]) + 44, f"{v4[0]}%", RED)
    for i, l in enumerate(lv[1:], 1):
        lab(xs[l], y(v9[i]) - 22, f"{v9[i]}%", NAVY)
        lab(xs[l], y(v35[i]) + (44 if l < 4 else -22), f"{v35[i]}%", MID)
    lab(xs[2], y(v4[1]) - 22, f"{v4[1]}%", RED)
    EX = xs[4] + 46
    lab(EX, y(v9[3]) + 10, "9b", NAVY, "start")
    lab(EX, y(v35[3]) + 12, "35b-a3b", MID, "start")
    lab(EX, y(0) - 4, f"4b {v4[3]}%", RED, "start")
    svg = "\n".join(s)

    r9 = val["qwen3.5:9b"][3] / val["qwen3.5:9b"][1]
    r35 = val["qwen3.5:35b-a3b"][3] / val["qwen3.5:35b-a3b"][1]
    assert r9 < 1 / 3 and r35 < 1 / 3  # 本文 89行「どちらも3分の1以下」

    html = header("hop-depth-levels", "「段数で崩れる」の折れ線 (本文 83-95行の表と文)。graph 条件 = 直下の材料だけ渡す、思考なし、温度0。",
                  "\n     集計: rows を condition=graph・model・level で絞り、exact の平均を % に丸める (analyze.py の「graph — 完全一致率」と同じ)") + f"""<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><style>
{BASE_CSS}
.side{{position:absolute;left:1190px;top:200px;width:360px;font-size:25px;line-height:1.55;font-weight:600;color:{SUB};}}
.side b{{color:{INK};font-weight:900;}}
.side .big{{font-size:30px;font-weight:900;color:{NAVY};line-height:1.35;margin-bottom:14px;}}
.side .r{{color:{RED};}}
.side p{{margin-bottom:18px;}}
</style></head><body>
<div class="t">段数を増やすと落ちる。<span>9b は3段目から崩れる</span></div>
<div class="s">グラフから1段ぶん (直下の材料だけ) 渡した条件の完全一致率。qwen3.5、思考なし、温度0</div>
<svg width="1600" height="900" viewBox="0 0 1600 900" style="position:absolute;inset:0">
{svg}
</svg>
<div class="side">
  <div class="big">2段 → 4段で<br>どちらも3分の1以下</div>
  <p>9b <b>{val['qwen3.5:9b'][1]}% → {val['qwen3.5:9b'][3]}%</b><br>35b-a3b <b>{val['qwen3.5:35b-a3b'][1]}% → {val['qwen3.5:35b-a3b'][3]}%</b></p>
  <p><b class="r">4b は2段で {val['qwen3.5:4b'][1]}%</b>。<br>実質1段で頭打ち</p>
  <p>1段は直下の材料が<br>答えそのもの。<br>2段からが同じ形式の<br>問題どうしの比較</p>
</div>
<div class="foot">5段 (2問) は表と同じく省いています。数字は nhop-bench の results/2026-09-05-qwen3.5-ladder.json から集計</div>
</body></html>
"""
    return html


# ---------------------------------------------------------------- slope
def slope_fig(d):
    rows = d["rows"]
    ms = ["qwen3.5:0.8b", "qwen3.5:2b", "qwen3.5:4b", "qwen3.5:9b", "qwen3.5:35b-a3b"]
    ex, rp = {}, {}
    for m in ms:
        b = sel(rows, model=m, condition="bare", min_level=2)
        g = sel(rows, model=m, condition="graph", min_level=2)
        assert len(b) == len(g) == 71
        ex[m] = (round(pct(b), 1), round(pct(g), 1))
        rp[m] = (round(mean(b, "recall"), 2), round(mean(b, "precision"), 2), round(mean(g, "recall"), 2), round(mean(g, "precision"), 2))
    # 本文 115-125行
    assert ex["qwen3.5:4b"] == (12.7, 1.4) and ex["qwen3.5:9b"] == (35.2, 49.3) and ex["qwen3.5:35b-a3b"] == (18.3, 31.0), ex
    assert ex["qwen3.5:0.8b"] == ex["qwen3.5:2b"] == (0.0, 0.0)
    assert rp["qwen3.5:4b"] == (0.26, 0.19, 0.33, 0.16), rp

    XL, XR, Y0, Y1 = 430, 800, 200, 680
    y = lambda v: Y1 - v / 55 * (Y1 - Y0)
    s = []
    for g in (0, 10, 20, 30, 40, 50):
        s.append(f'<line x1="140" x2="{XR+40}" y1="{y(g):.0f}" y2="{y(g):.0f}" stroke="#D3DCE7" stroke-width="2"/>')
        s.append(f'<text x="120" y="{y(g)+9:.0f}" text-anchor="end" font-size="24" fill="{SUB}" font-weight="600">{g}%</text>')
    for x, lab, sub in ((XL, "bare", "何も渡さない"), (XR, "graph", "直下の材料を渡す")):
        s.append(f'<line x1="{x}" x2="{x}" y1="{Y0-10}" y2="{Y1}" stroke="{SUB}" stroke-width="3"/>')
        s.append(f'<text x="{x}" y="{Y1+70}" text-anchor="middle" font-size="30" font-weight="900" fill="{INK}" font-family="DejaVu Sans Mono,monospace">{lab}</text>')
        s.append(f'<text x="{x}" y="{Y1+104}" text-anchor="middle" font-size="23" font-weight="600" fill="{SUB}">{sub}</text>')
    style = {"qwen3.5:9b": (NAVY, "9b"), "qwen3.5:35b-a3b": (MID, "35b-a3b"), "qwen3.5:4b": (RED, "4b")}
    for m in ("qwen3.5:0.8b",):
        a, b = ex[m]
        s.append(f'<line x1="{XL}" y1="{y(a):.0f}" x2="{XR}" y2="{y(b):.0f}" stroke="{PALE}" stroke-width="6"/>')
        s.append(f'<text x="{XL-20}" y="{y(a)+9:.0f}" text-anchor="end" font-size="26" font-weight="800" fill="#6B7B8D">0.8b・2b {a:.1f}%</text>')
        s.append(f'<text x="{XR+20}" y="{y(b)+30:.0f}" font-size="26" font-weight="800" fill="#6B7B8D">{b:.1f}%</text>')
    for m, (col, lab) in style.items():
        a, b = ex[m]
        w = 8
        s.append(f'<line x1="{XL}" y1="{y(a):.0f}" x2="{XR}" y2="{y(b):.0f}" stroke="{col}" stroke-width="{w}"/>')
        s.append(f'<circle cx="{XL}" cy="{y(a):.0f}" r="10" fill="{col}"/><circle cx="{XR}" cy="{y(b):.0f}" r="10" fill="{col}"/>')
        dyl = {"qwen3.5:4b": 22, "qwen3.5:35b-a3b": -4, "qwen3.5:9b": 9}[m]
        s.append(f'<text x="{XL-20}" y="{y(a)+dyl:.0f}" text-anchor="end" font-size="27" font-weight="900" fill="{col}">{lab} {a:.1f}%</text>')
        dyr = {"qwen3.5:4b": -8, "qwen3.5:35b-a3b": 9, "qwen3.5:9b": 9}[m]
        s.append(f'<text x="{XR+20}" y="{y(b)+dyr:.0f}" font-size="27" font-weight="900" fill="{col}">{b:.1f}%</text>')
    svg = "\n".join(s)
    r4 = rp["qwen3.5:4b"]
    html = header("hop-depth-slope", "「グラフは再現率を上げる。適合率を保てるのは容量次第」のスロープ図 (本文 113-136行の表と例)。2段以上 n=71、思考なし。",
                  "\n     集計: level>=2 の rows を model・condition で絞り、exact の平均 (%、小数1桁) と recall / precision の平均 (小数2桁)。analyze.py の「L2以上」と同じ\n"
                  "     右パネルの Spruce Stairs の例は本文 129-134行 (results の raw_response に同じ要素の応答がある。並び順も raw_response どおり)") + f"""<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><style>
{BASE_CSS}
.pn{{position:absolute;left:990px;top:180px;width:560px;height:600px;background:#fff;border:3px solid {RED};border-radius:16px;padding:26px 30px;}}
.pn .h{{font-size:30px;font-weight:900;color:{RED};}}
.pn table{{margin-top:16px;border-collapse:collapse;font-size:26px;}}
.pn td{{padding:6px 14px 6px 0;font-weight:700;}}
.pn td.v{{font-weight:900;color:{INK};}}
.pn .up{{color:{NAVY};font-weight:900;}}
.pn .dn{{color:{RED};font-weight:900;}}
.pn .ex{{margin-top:20px;border-top:2px solid #E1E7EF;padding-top:16px;font-size:24px;line-height:1.5;font-weight:600;color:{SUB};}}
.pn code{{font-family:'DejaVu Sans Mono','Noto Sans Mono',monospace;font-size:23px;color:{INK};font-weight:700;}}
.pn .ex b{{color:{INK};}}
</style></head><body>
<div class="t">グラフを渡すと、<span>4b だけ下がる</span></div>
<div class="s">2段以上 ({len(sel(rows, model='qwen3.5:4b', condition='graph', min_level=2))}問) の完全一致率。qwen3.5、思考なし、温度0</div>
<svg width="1600" height="900" viewBox="0 0 1600 900" style="position:absolute;inset:0">
{svg}
</svg>
<div class="pn">
  <div class="h">4b: 必要な物は入るが、<br>余計な物も入る</div>
  <table>
    <tr><td></td><td>bare</td><td></td><td>graph</td></tr>
    <tr><td>再現率</td><td class="v">{r4[0]:.2f}</td><td>→</td><td class="v">{r4[2]:.2f}</td><td class="up">上がる</td></tr>
    <tr><td>適合率</td><td class="v">{r4[1]:.2f}</td><td>→</td><td class="v">{r4[3]:.2f}</td><td class="dn">下がる</td></tr>
  </table>
  <div class="ex">
    <code>Spruce Stairs</code> 正解 <code>[spruce_log]</code><br>
    渡した直下の材料 <code>[spruce_planks]</code><br>
    graph の答え<br><code>["spruce_planks", "spruce_log"]</code><br>
    <b>渡された中間の名前 + 正しい材料</b>。<br>直前に見せられた語を答えから落とせない
  </div>
</div>
<div class="foot">再現率 = 正解の材料のうち答えに入った割合 / 適合率 = 答えのうち正解だった割合</div>
</body></html>
"""
    return html


# ---------------------------------------------------------------- think
def think_fig(d, t):
    m = "qwen3.5:35b-a3b"
    no = [round(pct(sel(d["rows"], model=m, condition=c, min_level=2)), 1) for c in ("bare", "graph")]
    th = [round(pct(sel(t["rows"], model=m, condition=c, min_level=2)), 1) for c in ("bare", "graph")]
    assert no == [18.3, 31.0] and th == [28.2, 19.7], (no, th)  # 本文 167-170行
    dn, dt = round(no[1] - no[0], 1), round(th[1] - th[0], 1)
    assert (dn, dt) == (12.7, -8.5)

    Y0, Y1 = 200, 700
    y = lambda v: Y1 - v / 40 * (Y1 - Y0)
    s = []
    for g in (0, 10, 20, 30, 40):
        s.append(f'<line x1="170" x2="1040" y1="{y(g):.0f}" y2="{y(g):.0f}" stroke="#D3DCE7" stroke-width="2"/>')
        s.append(f'<text x="150" y="{y(g)+9:.0f}" text-anchor="end" font-size="24" fill="{SUB}" font-weight="600">{g}%</text>')
    groups = [("思考なし", no, dn, 250), ("思考あり", th, dt, 660)]
    BW = 130
    for name, (b, g), diff, x0 in groups:
        for i, (v, col, lab) in enumerate(((b, PALE, "bare"), (g, NAVY, "graph"))):
            x = x0 + i * (BW + 30)
            s.append(f'<rect x="{x}" y="{y(v):.0f}" width="{BW}" height="{Y1-y(v):.0f}" fill="{col}"/>')
            s.append(f'<text x="{x+BW/2}" y="{y(v)-14:.0f}" text-anchor="middle" font-size="29" font-weight="900" fill="{INK}">{v:.1f}%</text>')
            s.append(f'<text x="{x+BW/2}" y="{Y1+36}" text-anchor="middle" font-size="26" font-weight="800" fill="{SUB}" font-family="DejaVu Sans Mono,monospace">{lab}</text>')
        s.append(f'<text x="{x0+BW+15}" y="{Y1+84}" text-anchor="middle" font-size="30" font-weight="900" fill="{INK}">{name}</text>')
        col = NAVY if diff > 0 else RED
        sign = "+" if diff > 0 else "−"
        # 差は群の上に置く (矢印は値ラベルと重なるので使わない)
        ytop = min(y(b), y(g)) - 70
        s.append(f'<text x="{x0+BW+15}" y="{ytop:.0f}" text-anchor="middle" font-size="36" font-weight="900" fill="{col}">graph で {sign}{abs(diff):.1f}</text>')
    s.append(f'<line x1="170" x2="1040" y1="{Y1}" y2="{Y1}" stroke="{SUB}" stroke-width="3"/>')
    defs = (f'<defs><marker id="au" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M0 0L10 5L0 10z" fill="{NAVY}"/></marker>'
            f'<marker id="ad" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M0 0L10 5L0 10z" fill="{RED}"/></marker></defs>')
    svg = defs + "\n" + "\n".join(s)
    html = header("hop-depth-think", "「大きいほうが強いとは限らない、ただし条件付き」の棒 (本文 163-174行の表と文)。35b-a3b、2段以上 n=71。",
                  f"\n     思考あり: nhop-bench/{THINK}\n"
                  "     集計: level>=2 の rows を condition で絞り exact の平均 (%、小数1桁)。差は graph − bare") + f"""<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><style>
{BASE_CSS}
.side{{position:absolute;left:1110px;top:200px;width:430px;font-size:25px;line-height:1.55;font-weight:600;color:{SUB};}}
.side .big{{font-size:31px;font-weight:900;color:{NAVY};line-height:1.4;margin-bottom:22px;}}
.side p{{margin-bottom:18px;}}
.side b{{color:{INK};font-weight:900;}}
.un{{display:inline-block;padding:1px 10px;border-radius:8px;font-size:22px;font-weight:800;background:#FFD58A;color:#0B1B2E;}}
</style></head><body>
<div class="t">35b-a3b は思考を入れると<span>符号が反転する</span></div>
<div class="s">2段以上 ({len(sel(t['rows'], model=m, condition='graph', min_level=2))}問) の完全一致率。bare = 何も渡さない、graph = 直下の材料を渡す</div>
<svg width="1600" height="900" viewBox="0 0 1600 900" style="position:absolute;inset:0">
{svg}
</svg>
<div class="side">
  <div class="big">思考は、想起には効き、<br>引きずられも強める</div>
  <p>思考ありで落ちた問題は、<br>4b と同じ型。渡された中間の<br>名前を混ぜるか、そこで止まる</p>
  <p>9b の思考ありは <span class="un">測れなかった</span><br>「35b は 9b より弱い」と<br>言えるのは、思考を切った条件だけ</p>
</div>
<div class="foot">思考なしは results/2026-09-05-qwen3.5-ladder.json、思考ありは results/2026-09-05-35b-think.json (nhop-bench) から集計</div>
</body></html>
"""
    return html


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out).expanduser()
    d, t = load(LADDER), load(THINK)
    assert t.get("think") is True
    for name, html in (("hop-depth-levels", levels_fig(d)), ("hop-depth-slope", slope_fig(d)), ("hop-depth-think", think_fig(d, t))):
        (out / f"{name}.html").write_text(html)
        print("wrote", out / f"{name}.html")


if __name__ == "__main__":
    main()
