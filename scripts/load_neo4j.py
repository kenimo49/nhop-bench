#!/usr/bin/env python3
"""datasets の関係を Neo4j に載せる。

  NEO4J_PASSWORD=... python3 scripts/load_neo4j.py

ノードは Item 1種類、エッジは INGREDIENT_OF 1種類だけ。
種類を増やす前に、1種類で問いに答えられるかを確かめる。
"""
import argparse, json, os, sys, time
from pathlib import Path
from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default="26.1")
    ap.add_argument("--uri", default=os.environ.get("NEO4J_URI", "bolt://localhost:7687"))
    ap.add_argument("--user", default=os.environ.get("NEO4J_USER", "neo4j"))
    ap.add_argument("--password", default=os.environ.get("NEO4J_PASSWORD"))
    a = ap.parse_args()

    # グラフには **全部** 載せる。曖昧で正解データから外した分も、
    # 捨てずに ambiguous フラグを立てて残す。
    # 「解決できない箇所を隠す」より「解決できない箇所を明示する」ほうが安全なため。
    sys.path.insert(0, str(ROOT))
    from nhopbench import minecraft, graph as g

    recipes, label, display, n_items = minecraft.load(a.version, ROOT / "data")
    ok, _ = g.build_dataset(recipes, label=label)          # 一意に展開できるもの
    unambiguous = set(ok)

    edges, nodes = set(), set()
    for out_id, variants in recipes.items():
        for ing in variants:
            for i in ing:
                edges.add((label(i), label(out_id)))
                nodes.add(label(i))
        nodes.add(label(out_id))

    rows = []
    for n in sorted(nodes):
        nid = next((k for k in recipes if label(k) == n), None)
        rows.append({
            "name": n,
            "display": display(nid) if nid is not None else n,
            "craftable": nid is not None and bool(recipes.get(nid)),
            "unambiguous": nid in unambiguous if nid is not None else False,
        })

    t0 = time.time()
    with GraphDatabase.driver(a.uri, auth=(a.user, a.password)) as drv:
        with drv.session() as s:
            s.run("MATCH (n:Item) DETACH DELETE n")
            s.run("CREATE CONSTRAINT item_name IF NOT EXISTS "
                  "FOR (i:Item) REQUIRE i.name IS UNIQUE")
            s.run("UNWIND $rows AS r MERGE (i:Item {name: r.name}) "
                  "SET i.display_name = r.display, i.craftable = r.craftable, "
                  "    i.unambiguous = r.unambiguous",
                  rows=rows)
            s.run("UNWIND $rows AS r "
                  "MATCH (a:Item {name: r.src}), (b:Item {name: r.dst}) "
                  "MERGE (a)-[:INGREDIENT_OF]->(b)",
                  rows=[{"src": x, "dst": y} for x, y in sorted(edges)])
            n = s.run("MATCH (i:Item) RETURN count(i) AS c").single()["c"]
            m = s.run("MATCH ()-[r:INGREDIENT_OF]->() RETURN count(r) AS c").single()["c"]
            u = s.run("MATCH (i:Item {unambiguous: true}) RETURN count(i) AS c").single()["c"]
    print(f"ノード {n} / エッジ {m} / 一意に展開できる {u}  ({time.time()-t0:.1f}秒)")


if __name__ == "__main__":
    main()
