#!/usr/bin/env python3
"""集計。

  python3 scripts/analyze.py results/2026-09-05-qwen3.5.json

**level 1 は既定で除外する。** 段数1では graph 条件が答えそのものを渡すため、
含めると「グラフが効いた」と読める数字が水増しされる。--include-l1 で見られる。
"""
import argparse, collections, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from nhopbench import scoring

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("--dataset", default=None)
    ap.add_argument("--include-l1", action="store_true")
    a = ap.parse_args()

    d = json.loads(Path(a.results).read_text())
    ds = json.loads((ROOT / (a.dataset or d["dataset"])).read_text())["items"]
    rows = d["rows"]
    models = list(dict.fromkeys(r["model"] for r in rows))
    levels = sorted({r["level"] for r in rows})

    print(f"# {Path(a.results).name}  {d['sample_size']}問  {d['elapsed_sec']}秒")
    print(f"# 段数別: {d['sample_by_level']}\n")

    for cond in ("bare", "graph"):
        sub = [r for r in rows if r["condition"] == cond]
        if not sub:
            continue
        print(f"## {cond} — 完全一致率 (%)\n")
        print(f"{'model':<18} " + "  ".join(f"L{l}" for l in levels) + "   parse失敗")
        for m in models:
            mr = [r for r in sub if r["model"] == m]
            cells = []
            for l in levels:
                lr = [r for r in mr if r["level"] == l]
                cells.append(f"{100*sum(r['exact'] for r in lr)/len(lr):4.0f}" if lr else "   -")
            print(f"{m:<18} {'  '.join(cells)}   {sum(1 for r in mr if not r['parsed'])}")
        print()

    lo = 1 if a.include_l1 else 2
    n = len({r["item"] for r in rows if r["level"] >= lo})
    print(f"## L{lo}以上 (n={n})  recall / precision と完全一致\n")
    print(f"{'model':<18} {'bare rec/prec':>15} {'graph rec/prec':>16} {'exact bare→graph':>22}")
    for m in models:
        o, ex = [], []
        for c in ("bare", "graph"):
            s = [r for r in rows if r["model"] == m and r["condition"] == c and r["level"] >= lo]
            if not s:
                o.append("   -   "); ex.append(0.0); continue
            o.append(f"{sum(r['recall'] for r in s)/len(s):.2f} / {sum(r['precision'] for r in s)/len(s):.2f}")
            ex.append(100 * sum(r["exact"] for r in s) / len(s))
        print(f"{m:<18} {o[0]:>15} {o[1]:>16} {ex[0]:8.1f}% →{ex[1]:6.1f}%  ({ex[1]-ex[0]:+.1f})")

    print("\n## 失敗の型 (bare, L2以上)\n")
    print(f"{'model':<18} {'exact':>7} {'途中で止まった':>15} {'誤り':>7} {'parse失敗':>10}")
    for m in models:
        mr = [r for r in rows if r["model"] == m and r["condition"] == "bare" and r["level"] >= 2]
        if not mr:
            continue
        c = collections.Counter(scoring.failure_kind(r, ds[r["item"]]) for r in mr)
        t = len(mr)
        print(f"{m:<18} {100*c['exact']/t:6.0f}% {100*c['stopped_early']/t:14.0f}% "
              f"{100*c['wrong']/t:6.0f}% {100*c['parse_fail']/t:9.0f}%")

    errs = collections.Counter(r["error"].split(":")[0] for r in rows if r.get("error"))
    if errs:
        print("\n## エラー:", dict(errs), "  ← 0% ではなく未計測として扱うこと")


if __name__ == "__main__":
    main()
