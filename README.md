# Step of create work enviromental

## UVによる環境作成

### 新規作成

適当なフォルダにて以下でプロジェクトを作成する

    uv init <プロジェクト名> -p <Pythonバージョン>

### パッケージ追加

パッケージを追加する場合は以下

    uv add <パッケージ名>

バージョン指定が必要なら以下

    uv add "<パッケージ名>==<バージョン>"

#### 証明書エラーの対応

uvはMozillaの証明書を利用しているため、環境によってはエラーになる場合がある。
対策として`--native-tls`フラグと共にコマンドを実行する。

    uv add <パッケージ名> --native-tls

恒久対策する場合は、

#### ローカルパッケージの追加

ローカルのパッケージを直接追加する場合は、`pyproject.toml`に追記する。
追記後、内容を反映するために`uv sync`を実行する。

    [project]
    dependencies = [
        # 相対パスまたは絶対パスで記述
        "package_name @ file:///path/to/package.whl",
    ]

### パッケージ削除

パッケージを取り除くなら以下

    uv remove <パッケージ名>

### 作成済み環境の同期

pyproject.tomlの存在するフォルダ内で以下コマンドを実行する

    uv sync
