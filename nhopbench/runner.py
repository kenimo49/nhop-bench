"""モデルに聞く。ollama (ローカル) と Anthropic API。

計測器の落とし穴が2つある。どちらも黙ってモデルの成績を下げる:

  num_predict を切らないと thinking 系が延々と生成し、返ってこない
  format を指定しないと小さいモデルが反復ループに落ち、配列が閉じずパース不能になる
"""
import json
import os
import urllib.request

ARRAY_SCHEMA = {"type": "array", "items": {"type": "string"}}


def ask_ollama(model: str, prompt: str, host: str, num_predict=300, timeout=180,
               think=False) -> str:
    """think=True にすると推論を有効にする。

    既定は False。有効にすると出力が長くなるので num_predict も一緒に上げること。
    MoE モデル (35b-a3b 等) は思考前提の設計なので、think を切ったまま
    「サイズの割に弱い」と結論しないこと (2026-09-05 に確認)。
    """
    body = json.dumps({
        "model": model, "stream": False, "think": think,
        "options": {"temperature": 0, "num_predict": num_predict},
        "format": ARRAY_SCHEMA,
        "prompt": prompt,
    }).encode()
    req = urllib.request.Request(f"{host}/api/generate", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read())
    # think=True かつ format 指定のとき、ollama は構造化出力を thinking 側に入れ
    # response を空で返すことがある (2026-09-05、qwen3.5:35b-a3b で確認)。
    # response だけ見ると全件パース失敗になり「思考を入れると悪化した」と誤読する。
    return (d.get("response") or "") + ("\n" + d["thinking"] if d.get("thinking") else "")


def ask_anthropic(model: str, prompt: str, max_tokens=512, timeout=120) -> str:
    body = json.dumps({"model": model, "max_tokens": max_tokens, "temperature": 0,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=body,
        headers={"x-api-key": os.environ["ANTHROPIC_API_KEY"],
                 "anthropic-version": "2023-06-01", "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read())
    return "".join(b.get("text", "") for b in d.get("content", []))
