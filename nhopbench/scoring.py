"""採点。集合の完全一致 / precision / recall と、失敗の型。"""
import json
import re


def normalize(s: str) -> str:
    s = str(s).strip().lower().replace("minecraft:", "")
    return re.sub(r"[\s-]+", "_", s).strip("_")


def parse_array(text: str):
    """応答から文字列配列を取り出す。取れなければ None。

    閉じていない配列も救済する。小さいモデルは反復ループに落ちて出力上限で途切れるが、
    そこまでに出した要素はモデルの答えなので、数えないと不当に低く出る。
    """
    for block in reversed(re.findall(r"\[[^\[\]]*\]", text or "", re.S)):
        try:
            v = json.loads(block)
            if isinstance(v, list) and all(isinstance(x, str) for x in v):
                return {normalize(x) for x in v if str(x).strip()}
        except Exception:
            continue
    i = (text or "").rfind("[")
    if i >= 0:
        items = re.findall(r'"([^"\n]{1,64})"', text[i:])
        if items:
            return {normalize(x) for x in items if x.strip()}
    return None


def score(pred, truth):
    if pred is None:
        return {"parsed": False, "exact": 0, "precision": 0.0, "recall": 0.0, "f1": 0.0}
    tp = len(pred & truth)
    p = tp / len(pred) if pred else 0.0
    r = tp / len(truth) if truth else 0.0
    return {"parsed": True, "exact": int(pred == truth), "precision": p, "recall": r,
            "f1": 2 * p * r / (p + r) if p + r else 0.0}


def failure_kind(row, item):
    """失敗の型。stopped_early = 直下の材料をそのまま答えた (展開せずに止まった)。

    「間違えた」と「途中で止まった」を混ぜると、
    「モデルは関係を知らない」という誤った結論になる。知っていて辿らない場合がある。
    """
    if not row["parsed"]:
        return "parse_fail"
    if row["exact"]:
        return "exact"
    if item["level"] >= 2:
        pred = parse_array(row.get("raw_response", ""))
        if pred is not None and pred == {normalize(x) for x in item["direct"]}:
            return "stopped_early"
    return "wrong"
