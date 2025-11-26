![AI Generated](https://img.shields.io/badge/AI-Generated-10B981?style=flat-square&logo=googlebard&logoColor=white)

# Step of create work enviromental

## UVによる環境作成

### 新規作成

適当なフォルダにて以下でプロジェクトを作成する

    uv init convert_with_rename_image

### パッケージ追加

以下パッケージを追加する

    uv add Pillow pillow-heif

テスト環境用は以下

    uv add pytest pytest-mock

### パッケージ削除

パッケージを取り除くなら以下

    uv remove <パッケージ名>

### 作成済み環境の同期

pyproject.tomlの存在するフォルダ内で以下コマンドを実行する

    uv sync
