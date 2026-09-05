#!/usr/bin/env python3
"""ベンチを回す。

  python3 scripts/run_bench.py --models qwen3.5:9b,qwen3.5:35b-a3b
  python3 scripts/run_bench.py --models claude-sonnet-5      # ANTHROPIC_API_KEY が要る

条件は2つ。
  bare   何も渡さない。モデルの記憶だけ
  graph  直下の材料だけを渡す。葉までの答えは渡さない (辿るのはモデルの仕事)

**level 1 は graph 条件が答えそのものを渡すことになる** (段数1では直下=葉)。
集計側で level>=2 に絞ること。level 1 で測れるのは指示追従の下限であって知識ではない。
"""
import argparse, json, os, random, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from nhopbench import prompts, runner, scoring

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SAMPLE = {1: 30, 2: 30, 3: 30, 4: 9, 5: 2}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="datasets/minecraft-pc-26.1.json")
    ap.add_argument("--models", required=True, help="カンマ区切り。claude* は Anthropic API")
    ap.add_argument("--host", default=os.environ.get("OLLAMA_HOST", "http://localhost:11434"))
    ap.add_argument("--seed", type=int, default=20260905)
    ap.add_argument("--limit", type=int, default=0, help="疎通確認用に問題数を絞る")
    ap.add_argument("--think", action="store_true", help="推論を有効にする (出力上限も上げる)")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    ds = json.loads((ROOT / a.dataset).read_text())
    items = ds["items"]
    by_level = {}
    for k, v in items.items():
        by_level.setdefault(v["level"], []).append(k)

    rnd = random.Random(a.seed)
    sample = []
    for lv, n in DEFAULT_SAMPLE.items():
        pool = sorted(by_level.get(lv, []))
        sample += rnd.sample(pool, min(n, len(pool)))
    if a.limit:
        sample = sample[:: max(1, len(sample) // a.limit)][: a.limit]

    models = [m.strip() for m in a.models.split(",") if m.strip()]
    rows, t0 = [], time.time()
    for model in models:
        for cond in ("bare", "graph"):
            hits = 0
            for i, key in enumerate(sample, 1):
                item = items[key]
                ctx = prompts.ONE_HOP.format(name=item["display_name"],
                                             direct=", ".join(item["direct"])) if cond == "graph" else ""
                prompt = prompts.MINECRAFT.format(name=item["display_name"], context=ctx)
                try:
                    txt = (runner.ask_anthropic(model, prompt) if model.startswith("claude")
                           else runner.ask_ollama(model, prompt, a.host,
                                                  num_predict=1500 if a.think else 300,
                                                  think=a.think, timeout=300))
                    err = None
                except Exception as e:
                    txt, err = "", f"{type(e).__name__}: {e}"
                s = scoring.score(scoring.parse_array(txt),
                                  {scoring.normalize(x) for x in item["leaves"]})
                hits += s["exact"]
                rows.append({"model": model, "condition": cond, "item": key,
                             "level": item["level"], **s, "error": err,
                             "raw_response": txt[:2000]})
                print(f"\r{model:<18} {cond:<5} {i}/{len(sample)} exact={hits}", end="", flush=True)
            print()

    out = {
        "dataset": a.dataset, "dataset_version": ds["version"], "seed": a.seed,
        "sample_size": len(sample), "think": a.think, "elapsed_sec": round(time.time() - t0, 1),
        "sample_by_level": {str(l): sum(1 for s in sample if items[s]["level"] == l)
                            for l in sorted(DEFAULT_SAMPLE)},
        "rows": rows,
    }
    p = Path(a.out) if a.out else ROOT / "results" / f"{time.strftime('%Y-%m-%d')}-run.json"
    p.parent.mkdir(exist_ok=True)
    p.write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(f"\n{len(rows)} 件 -> {p.relative_to(ROOT)}  ({out['elapsed_sec']}秒)")


if __name__ == "__main__":
    main()
