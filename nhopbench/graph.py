"""有向グラフ上の段数と展開。ドメインに依存しない部分。

グラフは {ノード: [材料集合, ...]} の形で受け取る。1ノードに複数の作り方がある。

段数 (level):
    level(x) = 0                      x を作る方法が無い (葉)
    level(x) = 1 + max(level(材料))   作り方がある

葉まで展開したときに答えが一意に決まるものだけを扱う。決まらないものは None を返して
呼び出し側で捨てる。曖昧なまま採点すると、正しい別解を誤りと数えることになる。
"""
from __future__ import annotations


class Expansion:
    __slots__ = ("level", "leaves", "direct")

    def __init__(self, level: int, leaves: frozenset, direct: frozenset):
        self.level = level
        self.leaves = leaves
        self.direct = direct

    def __repr__(self):
        return f"Expansion(level={self.level}, leaves={sorted(self.leaves)})"


def expand(node, recipes: dict, _stack=frozenset(), _memo=None):
    """葉まで展開する。一意に決まらなければ None。

    recipes[x] は「x を作る材料集合」の集合 (set of frozenset)。

    2つの曖昧さを別々に扱う:
      循環  探索中スタックに載る材料を要求する作り方は選択肢から外す。
            全部外れたら葉として扱う (鉄インゴット ⇄ 鉄ブロック ⇄ ナゲット がこれ)
      分岐  外した後に2通り以上残るなら None (どの木材でも可、など)
    """
    memo = {} if _memo is None else _memo
    if node in memo:
        return memo[node]

    options = [r for r in recipes.get(node, ()) if not (r & _stack)]
    if not options:
        memo[node] = Expansion(0, frozenset({node}), frozenset())
        return memo[node]
    if len(options) > 1:
        memo[node] = None
        return None

    direct = options[0]
    level, leaves = 0, set()
    for part in direct:
        sub = expand(part, recipes, _stack | {node}, memo)
        if sub is None:
            memo[node] = None
            return None
        level = max(level, sub.level)
        leaves |= sub.leaves
    memo[node] = Expansion(level + 1, frozenset(leaves), direct)
    return memo[node]


def build_dataset(recipes: dict, label=lambda n: n, min_level=1):
    """一意に展開できるノードだけを取り出す。

    葉が「実は作れる」ものを含むノードは落とす。9個⇄1個の圧縮ペア (小麦 ⇄ 干草の俵) が
    これに当たり、どこで止まるのが正解かが決まらない。
    """
    out, ambiguous, craftable_leaf = {}, 0, 0
    for node in recipes:
        e = expand(node, recipes, frozenset(), {})
        if e is None:
            ambiguous += 1
            continue
        if e.level < min_level:
            continue
        if any(recipes.get(i) for i in e.leaves):
            craftable_leaf += 1
            continue
        out[node] = {
            "label": label(node),
            "level": e.level,
            "leaves": sorted(label(i) for i in e.leaves),
            "direct": sorted(label(i) for i in e.direct),
        }
    return out, {"excluded_ambiguous": ambiguous, "excluded_craftable_leaf": craftable_leaf}
