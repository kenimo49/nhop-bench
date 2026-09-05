"""ドメイン: Minecraft のクラフトレシピをグラフにする。

元データは PrismarineJS/minecraft-data。**このリポジトリには置かない。**
LICENSE ファイルが無く再配布の条件が不明なため、実行時に取得して data/ に置く
(gitignore 済み)。派生した datasets/*.json だけを版管理する。
"""
import json
import urllib.request
from pathlib import Path

BASE = "https://raw.githubusercontent.com/PrismarineJS/minecraft-data/master/data/pc"


def fetch(version: str, name: str, cache_dir: Path) -> dict:
    cache_dir.mkdir(parents=True, exist_ok=True)
    p = cache_dir / f"{version}-{name}"
    if not p.exists():
        urllib.request.urlretrieve(f"{BASE}/{version}/{name}", p)
    return json.loads(p.read_text())


def _ingredients(recipe: dict) -> set:
    out = set()
    for row in (recipe.get("inShape") or []):
        for cell in row:
            if cell is not None:
                out.add(cell["id"] if isinstance(cell, dict) else cell)
    for cell in (recipe.get("ingredients") or []):
        if cell is not None:
            out.add(cell["id"] if isinstance(cell, dict) else cell)
    out.discard(None)
    return out


def load(version: str, cache_dir: Path):
    """(recipes, label) を返す。recipes[id] = {frozenset(材料id), ...}"""
    raw = fetch(version, "recipes.json", cache_dir)
    items = {i["id"]: i for i in fetch(version, "items.json", cache_dir)}
    recipes = {}
    for k, variants in raw.items():
        k = int(k)
        # 同じ材料集合の別配置は1つに畳む。自分自身を材料に含むレシピ (染色など) は除く
        recipes[k] = {frozenset(ing) for r in variants
                      if (ing := _ingredients(r)) and k not in ing}

    def label(i):
        return items[i]["name"] if i in items else str(i)

    def display(i):
        return items[i].get("displayName", label(i)) if i in items else str(i)

    return recipes, label, display, len(items)
