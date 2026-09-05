# データの出所

## クラフトデータ

このベンチマークのクラフト関係は [PrismarineJS/minecraft-data](https://github.com/PrismarineJS/minecraft-data)
から取得しています。

- **元データはこのリポジトリに含めていません。** `scripts/build_dataset.py` が実行時に取得し、
  `data/` に置きます (gitignore 済み)
- 理由: minecraft-data リポジトリに LICENSE ファイルが無く、再配布の条件が明示されていないため
  (npm パッケージ `minecraft-data` の package.json は MIT を宣言していますが、
  データリポジトリ側には対応する記載がありません)
- `datasets/*.json` は、そこから機械的に導出した**関係の一覧**です。元データの複製ではありません

## 商標

Minecraft は Mojang Synergies AB の商標です。
このプロジェクトは Mojang Studios および Microsoft とは無関係で、承認も後援も受けていません。
プロジェクト名およびパッケージ名に Minecraft の名称は使用していません。

## 引用している先行研究

ホップ数を軸にした評価が見当たらないことが、このベンチマークの動機です。
既存のものはタスクの成否で測っています。

- Plancraft — クラフトを計画能力のベンチマークにしたもの
- Orak — 複数ゲームでの LLM エージェント評価
- "From Entity-Centric to Goal-Oriented Graphs: Enhancing LLM Knowledge Retrieval in Minecraft"
