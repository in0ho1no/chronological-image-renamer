import os
import shutil
from datetime import datetime

from PIL import Image
from pillow_heif import register_heif_opener

# HEIC形式をPillowで扱えるように登録
register_heif_opener()


def get_date_taken(path: str) -> tuple[datetime, str]:
    """
    画像の撮影日時を取得する関数。
    複数のEXIFタグを走査し、失敗した場合はファイルの更新日時を使用します。
    戻り値: (datetimeオブジェクト, 取得元の説明文字列)
    """
    try:
        img = Image.open(path)
        exif = img.getexif()

        if exif:
            # チェックするタグの優先順位
            # 36867: DateTimeOriginal (撮影日時)
            # 36868: DateTimeDigitized (デジタル化日時)
            # 306:   DateTime (変更日時)
            target_tags = [36867, 36868, 306]

            for tag in target_tags:
                date_str = exif.get(tag)
                if date_str:
                    try:
                        # 一般的なEXIF日付形式: 'YYYY:MM:DD HH:MM:SS'
                        # まれにデータ破損で空文字や不正な文字が入ることがあるためtryで囲む
                        dt = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
                        return dt, 'EXIF'
                    except ValueError:
                        continue
    except Exception:
        pass

    # EXIFが取得できない場合はファイルの更新日時(mtime)を使用
    timestamp = os.path.getmtime(path)
    return datetime.fromtimestamp(timestamp), 'FileTimestamp(更新日時)'


def process_images(input_dir: str) -> None:
    """
    画像変換・リネーム処理のメイン関数
    """
    # 出力ディレクトリの設定(カレントディレクトリ内の converted)
    output_dir = os.path.join(os.getcwd(), 'converted')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    target_exts = ('.jpg', '.jpeg', '.heic')
    files = [f for f in os.listdir(input_dir) if f.lower().endswith(target_exts)]

    if not files:
        print('画像が見つかりません。')
        return

    print(f'--- 日付情報の解析中 ({len(files)}枚) ---')

    # 撮影日時とファイルパスのペアを作成
    files_with_date = []
    for f in files:
        full_path = os.path.join(input_dir, f)
        date_taken, source = get_date_taken(full_path)

        # 確認用ログ(ここでおかしい日付になっていないか確認してください)
        print(f'[{source}] {date_taken} : {f}')

        files_with_date.append((date_taken, full_path, f))

    # ソート実行
    # 第1キー: 日時, 第2キー: 元のファイル名(日時が全く同じ場合の対策)
    files_with_date.sort(key=lambda x: (x[0], x[2]))

    print('\n--- 変換・コピー開始 ---')

    for idx, (_, src_path, original_filename) in enumerate(files_with_date, start=1):
        new_filename = f'IMG_{idx:04d}.jpg'
        dst_path = os.path.join(output_dir, new_filename)
        ext = os.path.splitext(original_filename)[1].lower()

        try:
            if ext in ['.jpg', '.jpeg']:
                shutil.copy2(src_path, dst_path)
                print(f'Copy: {new_filename} <- {original_filename}')

            elif ext == '.heic':
                img = Image.open(src_path)
                exif_bytes = img.info.get('exif')

                if exif_bytes:
                    img.convert('RGB').save(dst_path, 'JPEG', quality=95, exif=exif_bytes)
                else:
                    img.convert('RGB').save(dst_path, 'JPEG', quality=95)

                print(f'Conv: {new_filename} <- {original_filename}')

        except Exception as e:
            print(f'Error: {original_filename} -> {e}')

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
