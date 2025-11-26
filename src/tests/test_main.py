import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# main.py がルートにあると仮定してパスを通す
sys.path.append(str(Path(__file__).parent.parent))

from main import BatchRenamer, ImageFile


class TestImageFile:
    """ImageFileクラスの単体テスト."""

    @pytest.fixture
    def mock_path(self, tmp_path: Path) -> Path:
        """テスト用のダミーファイルパスを生成するフィクスチャ."""
        p = tmp_path / 'test_image.jpg'
        p.touch()
        return p

    def test_date_taken_from_exif(self, mock_path: Path) -> None:
        """EXIF情報から日付が正しく取得できるかテスト."""
        target_date_str = '2023:01:01 12:00:00'
        expected_date = datetime(2023, 1, 1, 12, 0, 0)

        # PIL.Image.open をモック化
        with patch('main.Image.open') as mock_open:
            # getexif() が返す辞書を定義 (36867 = DateTimeOriginal)
            mock_img = MagicMock()
            mock_img.getexif.return_value = {36867: target_date_str}

            # コンテキストマネージャ (__enter__) の戻り値を設定
            mock_open.return_value.__enter__.return_value = mock_img

            img_file = ImageFile(mock_path)

            assert img_file.date_taken == expected_date
            assert img_file.source_info == 'EXIF'

    def test_date_taken_fallback_mtime(self, mock_path: Path) -> None:
        """EXIFがない場合にファイルの更新日時が使われるかテスト."""
        # PIL.Image.open が失敗、あるいはEXIFがない状態をシミュレート
        with patch('main.Image.open') as mock_open:
            mock_img = MagicMock()
            mock_img.getexif.return_value = {}  # 空のEXIF
            mock_open.return_value.__enter__.return_value = mock_img

            # ファイルの更新日時を設定 (2024-01-01 10:00:00)
            ts = datetime(2024, 1, 1, 10, 0, 0).timestamp()
            # pathlib.Path.stat().st_mtime をモックしたいが、
            # 実際のファイルシステム(tmp_path)を使っているため os.utime で時間をセットする
            import os

            os.utime(mock_path, (ts, ts))

            img_file = ImageFile(mock_path)

            assert img_file.date_taken == datetime(2024, 1, 1, 10, 0, 0)
            assert img_file.source_info == 'FileTimestamp'

    def test_sorting_order(self, tmp_path: Path) -> None:
        """__lt__ メソッドによるソート順序のテスト."""
        # ファイル実体は不要なのでPathオブジェクトのみ作成
        p1 = tmp_path / 'A.jpg'
        p2 = tmp_path / 'B.jpg'
        p3 = tmp_path / 'C.jpg'

        img1 = ImageFile(p1)
        img2 = ImageFile(p2)
        img3 = ImageFile(p3)

        # _date_taken を強制的にセットして解析ロジックをバイパス
        img1._date_taken = datetime(2023, 1, 1, 10, 0, 0)
        img2._date_taken = datetime(2023, 1, 1, 12, 0, 0)  # img1より新しい
        img3._date_taken = datetime(2023, 1, 1, 10, 0, 0)  # img1と同じ日時

        # リスト作成
        images = [img2, img3, img1]
        images.sort()

        # 期待される順序:
        # 1. img1 (日時が古い)
        # 2. img3 (日時はimg1と同じだが、ファイル名が 'C.jpg' > 'A.jpg' なのでimg1より後...
        #    修正: 実装は filename < other.filename なので 'A' < 'C'。
        #    よって [img1, img3, img2] の順になるはず

        assert images[0] == img1  # 10:00, A.jpg
        assert images[1] == img3  # 10:00, C.jpg
        assert images[2] == img2  # 12:00, B.jpg


class TestBatchRenamer:
    """BatchRenamerクラスの統合テスト."""

    @pytest.fixture
    def source_dir(self, tmp_path: Path) -> Path:
        """テスト用の入力ディレクトリとダミーファイルを作成."""
        src = tmp_path / 'source'
        src.mkdir()

        # ダミーファイル作成 (中身は空でOK、ロジックテストではモックを使うため)
        (src / 'test1.jpg').touch()
        (src / 'test2.HEIC').touch()  # 大文字拡張子の確認
        (src / 'ignore.txt').touch()  # 無視されるべきファイル

        return src

    def test_collect_images(self, source_dir: Path) -> None:
        """対象の拡張子だけが収集されるかテスト."""
        renamer = BatchRenamer(str(source_dir))
        images = renamer._collect_images()

        filenames = sorted([img.path.name for img in images])
        assert filenames == ['test1.jpg', 'test2.HEIC']
        assert len(images) == 2

    def test_run_flow(self, source_dir: Path) -> None:
        """runメソッドの全体フローテスト.

        実際の画像変換(export)は重いためモック化し、
        ファイルのリネームロジックが正しく回るかを確認する。
        """
        renamer = BatchRenamer(str(source_dir))

        # 1. export: 実際のファイル書き込みを防ぐためのモック
        # 2. _parse_date: 内部状態(_date_taken)を操作してソート順を制御するためのモック
        #    autospec=Trueにすることで、side_effectの第一引数にself(インスタンス)が渡されるようになる
        with patch('main.ImageFile.export') as mock_export, patch('main.ImageFile._parse_date', autospec=True) as mock_parse:
            # 型アノテーションを追加 (Function is missing a type annotation 対策)
            def assign_date_side_effect(self_obj: ImageFile) -> None:
                # ファイル名に 'test1' が含まれていたら古い日付、それ以外は新しい日付にする
                if 'test1' in self_obj.path.name:
                    self_obj._date_taken = datetime(2023, 1, 1)
                else:
                    self_obj._date_taken = datetime(2023, 1, 2)
                # 取得元もセットしておかないと source_info プロパティで再解析が走ってしまう
                self_obj._date_source = 'Mock'

            # 変数 mock_parse を使用する (Local variable assigned but never used 対策)
            mock_parse.side_effect = assign_date_side_effect

            renamer.run()

            # 検証: ファイルが2つあるので export は2回呼ばれるはず
            assert mock_export.call_count == 2

            # 検証: 出力ファイル名の連番チェック
            # call_args_list から引数を抽出: call(Path(...)) -> args[0] is Path
            args_list = mock_export.call_args_list
            dest_paths = [args.args[0] for args in args_list]
            filenames = sorted([p.name for p in dest_paths])

            # ソートが正しく機能していれば、test1(古い) -> IMG_0001, test2(新しい) -> IMG_0002 となる
            assert filenames == ['IMG_0001.jpg', 'IMG_0002.jpg']

            # 検証: 出力ディレクトリが作成されているか
            assert (source_dir / 'converted').exists()
