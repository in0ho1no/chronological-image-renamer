import shutil
from datetime import datetime
from pathlib import Path

from PIL import Image
from pillow_heif import register_heif_opener

# グローバル設定: HEIC形式をPillowで扱えるように登録
register_heif_opener()


class ImageFile:
    """個々の画像ファイルを表現するクラス

    EXIF情報の取得、比較、変換保存の責務を持つ。
    """

    # 優先順位順のEXIFタグID
    EXIF_TAGS = (
        36867,  # DateTimeOriginal
        36868,  # DateTimeDigitized
        306,  # DateTime
    )
    DATE_FORMAT = '%Y:%m:%d %H:%M:%S'

    def __init__(self, path: Path) -> None:
        """初期化

        Args:
            path (Path): 画像ファイルのパス
        """
        self.path: Path = path
        self._date_taken: datetime | None = None
        self._date_source: str = ''

    @property
    def date_taken(self) -> datetime:
        """撮影日時を返す

        Returns:
            datetime: 撮影日時。取得できない場合は更新日時。
        """
        if self._date_taken is None:
            self._parse_date()
        # _parse_date実行後は必ず値が入るロジックだが、Mypyのためにassertする
        assert self._date_taken is not None
        return self._date_taken

    @property
    def source_info(self) -> str:
        """日付の取得元情報を返す

        Returns:
            str: 'EXIF' または 'FileTimestamp'
        """
        if not self._date_source:
            self._parse_date()
        return self._date_source

    def _parse_date(self) -> None:
        """EXIFまたはファイル更新日時から日付を解析する"""
        try:
            with Image.open(self.path) as img:
                exif = img.getexif()
                if exif:
                    for tag in self.EXIF_TAGS:
                        date_str = exif.get(tag)
                        if date_str:
                            try:
                                self._date_taken = datetime.strptime(date_str, self.DATE_FORMAT)
                                self._date_source = 'EXIF'
                                return
                            except ValueError:
                                continue
        except Exception:
            pass

        # EXIF取得失敗時はファイルの更新日時を使用
        timestamp = self.path.stat().st_mtime
        self._date_taken = datetime.fromtimestamp(timestamp)
        self._date_source = 'FileTimestamp'

    def export(self, output_path: Path) -> None:
        """ファイルを指定のパスに変換/コピーして保存する

        Args:
            output_path (Path): 出力先のパス
        """
        suffix = self.path.suffix.lower()

        try:
            if suffix in ('.jpg', '.jpeg'):
                shutil.copy2(self.path, output_path)
                print(f'Copy: {output_path.name} <- {self.path.name}')

            elif suffix == '.heic':
                self._convert_heic_to_jpg(output_path)
                print(f'Conv: {output_path.name} <- {self.path.name}')

        except Exception as e:
            print(f'Error: {self.path.name} -> {e}')

    def _convert_heic_to_jpg(self, output_path: Path) -> None:
        """HEICをJPGに変換して保存

        Args:
            output_path (Path): 保存先のパス
        """
        with Image.open(self.path) as img:
            exif_bytes = img.info.get('exif')
            rgb_img = img.convert('RGB')

            save_kwargs = {'quality': 95}
            if exif_bytes:
                save_kwargs['exif'] = exif_bytes

            rgb_img.save(output_path, 'JPEG', **save_kwargs)

    def __lt__(self, other: object) -> bool:
        """ソート用のマジックメソッド (<)

        Args:
            other (object): 比較対象

        Returns:
            bool: selfの方が日時が古い(または名前が若い)場合にTrue
        """
        if not isinstance(other, ImageFile):
            return NotImplemented
        if self.date_taken != other.date_taken:
            return self.date_taken < other.date_taken
        return self.path.name < other.path.name


class BatchRenamer:
    """ディレクトリ単位での画像処理フローを管理するクラス"""

    TARGET_EXTS = ('.jpg', '.jpeg', '.heic')

    def __init__(self, input_dir: str, output_dirname: str = 'converted') -> None:
        """初期化

        Args:
            input_dir (str): 入力ディレクトリのパス
            output_dirname (str): 出力ディレクトリ名. Defaults to 'converted'.
        """
        self.input_dir = Path(input_dir)
        self.output_dir = self.input_dir / output_dirname

    def run(self) -> None:
        """処理のメインフロー"""
        if not self.input_dir.exists():
            print(f'エラー: 指定されたフォルダが見つかりません: {self.input_dir}')
            return

        print(f'検索対象: {self.input_dir}')

        # 画像ファイルの収集とオブジェクト化
        images = self._collect_images()

        if not images:
            print('画像が見つかりません。')
            return

        print(f'--- 日付情報の解析中 ({len(images)}枚) ---')
        # 解析(プロパティアクセス時に実行されるが、ここでログ出力のために一度アクセス)
        for img in images:
            print(f'[{img.source_info}] {img.date_taken} : {img.path.name}')

        # ソート実行 (ImageFileクラスの __lt__ が使われる)
        images.sort()

        # 変換・出力処理
        self._prepare_output_dir()
        print('\n--- 変換・コピー開始 ---')

        for idx, img in enumerate(images, start=1):
            new_filename = f'IMG_{idx:04d}.jpg'
            dst_path = self.output_dir / new_filename
            img.export(dst_path)

        print('\n処理が完了しました。')

    def _collect_images(self) -> list[ImageFile]:
        """対象拡張子のファイルを検索し、ImageFileオブジェクトのリストを返す

        Returns:
            list[ImageFile]: 画像オブジェクトのリスト
        """
        return [ImageFile(p) for p in self.input_dir.iterdir() if p.is_file() and p.suffix.lower() in self.TARGET_EXTS]

    def _prepare_output_dir(self) -> None:
        """出力ディレクトリの作成"""
        self.output_dir.mkdir(exist_ok=True)


if __name__ == '__main__':
    # 設定: 入力フォルダのパス
    TARGET_FOLDER = r'C:\Users\seigy\Desktop\20251123'

    renamer = BatchRenamer(TARGET_FOLDER)
    renamer.run()
