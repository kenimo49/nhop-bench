"""課題文。

止まる場所を例つきで書くこと。「作れないものまで展開せよ」とだけ書くと、
モデルが精錬の1段先まで正しく展開した答え (glass ではなく sand) を誤りと採点してしまう。
2026-09-05 に1回目の実験を丸ごと捨てた原因がこれ。
"""

MINECRAFT = """In Minecraft (Java Edition), list the materials required to craft one {name}.

Expand every CRAFTING step, and stop there. An item that is NOT obtained by crafting is a
stopping point -- items you mine, smelt, harvest, trade for, or get as a mob drop.
Examples of stopping points: stone (smelted from cobblestone), glass (smelted from sand),
brick (smelted from clay ball), oak_log (chopped), diamond (mined).
Do NOT go past a stopping point, and do not list intermediate crafted items.
{context}
Answer with ONLY a JSON array of snake_case item ids, nothing else.
Example format: ["cobblestone", "quartz"]"""

# graph 条件で足す文脈。**直下の材料しか渡さない。**
# 葉まで展開した答えを渡すと「写せるか」しか測れない。
ONE_HOP = """
Known (from a crafting graph): one {name} is crafted directly from: {direct}.
The items above may themselves be craftable -- keep expanding until you reach stopping points.
"""
