![AI Generated](https://img.shields.io/badge/AI-Generated-10B981?style=flat-square&logo=googlebard&logoColor=white)
![Tests](https://github.com/in0ho1no/chronological-image-renamer/actions/workflows/unittest.yml/badge.svg)

# chronological-image-renamer

EXIF撮影日時に基づいて画像を時系列順にソート・変換（HEIC対応）・リネームするPythonツールです。
AI（Gemini）との対話を通じてリファクタリングされた、モダンなPython実装（オブジェクト指向・型安全）を採用しています。

## 特徴

* **HEIC対応**: iPhone等のHEIC形式を自動でJPGに変換して保存します。
* **EXIF解析**: 画像の撮影日時（`DateTimeOriginal` 等）を優先的に読み取ります。
* **スマートなソート**: 撮影日時順に並べ替え、連番（`IMG_0001.jpg`...）を付与します。
* **フォールバック機能**: EXIF情報がない画像は、ファイルの更新日時を使用してソートします。
* **安全性**: 元のファイルは変更せず、`converted` ディレクトリに新しいファイルを生成します。

## 必要要件

* Python 3.12 以上
* [uv](https://github.com/astral-sh/uv)

## 環境構築

リポジトリをクローンし、`pyproject.toml` が存在するディレクトリで以下のコマンドを実行してください。これだけで仮想環境の作成と依存ライブラリのインストールが完了します。

```bash
uv sync
```

## 使い方

1.  `main.py` を開き、最下部の `TARGET_FOLDER` 変数を、処理したい画像が入っているフォルダのパスに変更してください。

    ```python
    if __name__ == '__main__':
        # ここに対象フォルダのパスを指定してください
        TARGET_FOLDER = r'C:\Users\YourName\Pictures\TargetFolder'
        
        renamer = BatchRenamer(TARGET_FOLDER)
        renamer.run()
    ```

2.  以下のコマンドでスクリプトを実行します。

    ```bash
    uv run main.py
    ```

実行後、指定したフォルダの中に `converted` フォルダが作成され、処理済みの画像が保存されます。

## 開発・テスト

このプロジェクトは `ruff` によるLint/Formatと、`mypy` による型チェック、`pytest` によるテスト済みです。

### テストの手動実行

```bash
# 依存関係のインストール（pytest含む）
uv sync

# テストの実行
uv run pytest
```

### コード品質チェック

```bash
# 型チェック
uv run mypy main.py

# Lintチェック
uv run ruff check main.py
```

## ライセンス

MIT License
