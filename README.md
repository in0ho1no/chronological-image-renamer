# Step of create work enviromental

## UVによる環境作成

### 新規作成

適当なフォルダにて以下でプロジェクトを作成する

    uv init convert_with_rename_image

### パッケージ追加

パッケージを追加する場合は以下

    uv add Pillow pillow-heif

### パッケージ削除

パッケージを取り除くなら以下

    uv remove <パッケージ名>

### 作成済み環境の同期

pyproject.tomlの存在するフォルダ内で以下コマンドを実行する

    uv sync
