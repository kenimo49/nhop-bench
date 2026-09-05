#!/usr/bin/env python3
"""正解データを作る。人手のアノテーションは挟まない。

  python3 scripts/build_dataset.py --version 26.1
"""
import argparse, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from nhopbench import graph, minecraft

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default="26.1")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    recipes, label, display, n_items = minecraft.load(a.version, ROOT / "data")
    items, stats = graph.build_dataset(recipes, label=label)
    for k, v in items.items():
        v["display_name"] = display(k)

    edges = sum(len(set().union(*r)) for r in recipes.values() if r)
    levels = {}
    for v in items.values():
        levels[str(v["level"])] = levels.get(str(v["level"]), 0) + 1

    out = {
        "domain": "minecraft",
        "version": a.version,
        "source": f"{minecraft.BASE}/{a.version}/recipes.json",
        "source_project": "PrismarineJS/minecraft-data",
        "generated_by": "scripts/build_dataset.py",
        "items_total": n_items,
        "craftable_total": len(recipes),
        "edges": edges,
        **stats,
        "level_distribution": dict(sorted(levels.items())),
        "items": {label(k): {kk: vv for kk, vv in v.items()} for k, v in items.items()},
    }
    p = Path(a.out) if a.out else ROOT / "datasets" / f"minecraft-pc-{a.version}.json"
    p.parent.mkdir(exist_ok=True)
    p.write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(f"minecraft-data {a.version}")
    print(f"  items            {n_items}")
    print(f"  craftable        {len(recipes)}")
    print(f"  edges            {edges}")
    print(f"  excluded (分岐)   {stats['excluded_ambiguous']}")
    print(f"  excluded (可craft葉) {stats['excluded_craftable_leaf']}")
    print(f"  dataset          {len(items)}  levels {out['level_distribution']}")
    print(f"  -> {p.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
