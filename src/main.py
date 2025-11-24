import os
import shutil
from datetime import datetime

from PIL import Image
from pillow_heif import register_heif_opener

# HEIC形式をPillowで扱えるように登録
register_heif_opener()


def get_date_taken(path: str) -> datetime:
    """
    画像の撮影日時を取得する関数。
    EXIF情報(DateTimeOriginal)を取得し、失敗した場合はファイルの更新日時を使用します。
    """
    try:
        img = Image.open(path)

        # _getexif() ではなく、公式APIの getexif() を使用します
        exif = img.getexif()

        if exif:
            # DateTimeOriginal のタグIDは 36867 です
            date_str = exif.get(36867)

            if date_str:
                # 日付フォーマットが正しいか確認しつつ変換
                return datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')

    except Exception:
        # 読み込みエラーや日付フォーマット違いなどは無視してタイムスタンプへ
        pass

    # EXIFが取得できない場合はファイルの更新日時(mtime)を使用
    timestamp = os.path.getmtime(path)
    return datetime.fromtimestamp(timestamp)


def process_images(input_dir: str) -> None:
    """
    画像変換・リネーム処理のメイン関数
    """
    # 出力ディレクトリの設定(カレントディレクトリ内の converted)
    output_dir = os.path.join(os.getcwd(), 'converted')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f'フォルダ作成: {output_dir}')

    # 対象の拡張子
    target_exts = ('.jpg', '.jpeg', '.heic')

    # ファイルリストの取得
    files = [f for f in os.listdir(input_dir) if f.lower().endswith(target_exts)]

    print(f'合計 {len(files)} 枚の画像を検出しました。日付順に並べ替えています...')

    # 撮影日時とファイルパスのペアを作成してソート
    files_with_date = []
    for f in files:
        full_path = os.path.join(input_dir, f)
        date_taken = get_date_taken(full_path)
        files_with_date.append((date_taken, full_path, f))

    # 日付順(昇順)にソート
    files_with_date.sort(key=lambda x: x[0])

    print('変換・コピーを開始します...')

    # 変換・コピー処理
    for idx, (_, src_path, original_filename) in enumerate(files_with_date, start=1):
        # 連番ファイル名の生成 (例: IMG_0001.jpg)
        new_filename = f'IMG_{idx:04d}.jpg'
        dst_path = os.path.join(output_dir, new_filename)

        ext = os.path.splitext(original_filename)[1].lower()

        try:
            if ext in ['.jpg', '.jpeg']:
                # JPGの場合: メタデータを保持してコピー
                shutil.copy2(src_path, dst_path)
                print(f'[{idx}] Copy (JPG): {original_filename} -> {new_filename}')

            elif ext == '.heic':
                # HEICの場合: JPGに変換して保存
                img = Image.open(src_path)

                # EXIF情報を取得(そのままバイナリとして保持)
                exif_bytes = img.info.get('exif')

                # 保存(EXIFがある場合は埋め込む)
                if exif_bytes:
                    img.convert('RGB').save(dst_path, 'JPEG', quality=95, exif=exif_bytes)
                else:
                    img.convert('RGB').save(dst_path, 'JPEG', quality=95)

                print(f'[{idx}] Convert (HEIC): {original_filename} -> {new_filename}')

        except Exception as e:
            print(f'エラー発生 ({original_filename}): {e}')

    print('\n処理が完了しました。')


if __name__ == '__main__':
    # ここに入力フォルダのパスを指定してください
    target_folder = r'C:\Users\seigy\Desktop\20251123-1-001\20251123'

    # フォルダが存在するか確認
    if os.path.exists(target_folder):
        process_images(target_folder)
    else:
        print(f'エラー: 指定されたフォルダが見つかりません: {target_folder}')
        print("スクリプト内の 'target_folder' 変数を正しいパスに書き換えてください。")
