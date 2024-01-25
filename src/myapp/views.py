import re
import unicodedata
from django import forms
from PIL import Image
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.shortcuts import render
from dotenv import load_dotenv
import openai
from openai import OpenAIError
import pytesseract
import os

# .env ファイルから環境変数を読み込む
load_dotenv()

class ImageUploadForm(forms.Form):
    image = forms.ImageField()

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            main, sub = image.content_type.split('/')
            if not (main == 'image' and sub in ['jpeg', 'pjpeg', 'png', 'gif']):
                raise ValidationError(_('JPEG、PNG、またはGIF形式の画像を使用してください。'))
            if image.size > 5*1024*1024:  # 5MB
                raise ValidationError(_('ファイルサイズは5MB以下にしてください。'))

            # 画像のアスペクト比と解像度をチェック
            pil_image = Image.open(image)
            width, height = pil_image.size
            aspect_ratio = width / height
            resolution = width * height
            if aspect_ratio < 1 or aspect_ratio > 2:  # アスペクト比が1から2の範囲外
                raise ValidationError(_('画像のアスペクト比は1から2の間にしてください。'))
            if resolution < 100*100 or resolution > 2000*2000:  # 解像度が100x100から2000x2000の範囲外
                raise ValidationError(_('画像の解像度は100x100から2000x2000の間にしてください。'))
        return image

def preprocess_input(text, language='en'):
    # 特殊文字の置換
    text = text.replace('&', 'and')

    # 正規化
    if language == 'ja':
        # 日本語の正規化 (全角半角、ひらがなカタカナの統一)
        text = unicodedata.normalize('NFKC', text)
    elif language == 'en':
        # 英語の正規化 (小文字化)
        text = text.lower()

    # ストップワードの削除
    stop_words = get_stop_words(language)  # 対応する言語のストップワードリストを取得
    text_tokens = text.split()
    text_tokens = [token for token in text_tokens if token not in stop_words]
    text = ' '.join(text_tokens)

    # HTMLタグの削除
    text = re.sub(r'<.*?>', '', text)

    # 特定のパターンの除去
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'\(.*?\)', '', text)  # 仮の特定のパターンを除去する正規表現

    return text

def get_stop_words(language):
    # 言語に対応するストップワードリストを返す
    if language == 'ja':
        return ['の', 'と', 'です', 'ます']  # 仮の日本語ストップワードリスト
    elif language == 'en':
        return ['the', 'and', 'is', 'in', 'on', 'at']  # 仮の英語ストップワードリスト
    else:
        return []

def extract_keywords(image_path, language='en'):
    # 画像からテキストへの変換
    text = pytesseract.image_to_string(Image.open(image_path), lang=language)
    return preprocess_input(text, language)

def summarize_information(text, language='en'):
    # .env ファイルから API キーを取得
    api_key = os.getenv('OPENAI_API_KEY')
    
    if api_key:
        # API キーが存在する場合にのみ OpenAI クライアントを初期化
        openai.api_key = api_key

        # 問題文の生成
        chat_models = openai.ChatCompletion.create(
            model="gpt-4-vision-preview",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": preprocess_input(text, language)},
            ]
        )
        result = preprocess_input(chat_models['choices'][0]['message']['content'], language)
        return postprocess_output(result)
    else:
        # API キーが見つからない場合はエラーを返す
        raise OpenAIError("API key not found. Set the OPENAI_API_KEY environment variable.")

def postprocess_output(result):
    # 余分な空白や改行の削除
    cleaned_result = result.strip()

    # 特殊文字の処理（例: 置換や削除など）
    cleaned_result = cleaned_result.replace('...', '…')  # 例として「...」を特定の文字に置換

    return cleaned_result

def handle_uploaded_file(f):
    filename = f.name
    destination_dir = 'uploaded_images'
    os.makedirs(destination_dir, exist_ok=True)  # ディレクトリが存在しない場合には作成
    destination_path = os.path.join(destination_dir, filename)
    try:
        with open(destination_path, 'wb+') as destination:
            for chunk in f.chunks():
                destination.write(chunk)
    except Exception as e:
        print(f"An error occurred while saving the file: {e}")
        return None, str(e)
    return destination_path, None

def upload_image(request):
    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            image_path, error = handle_uploaded_file(request.FILES['image'])
            if image_path is None:
                form.add_error(None, f'画像の保存中にエラーが発生しました: {error}')
            else:
                # 画像のアップロードが成功した場合の処理をここに書く
                keywords = extract_keywords(image_path)
                summary = summarize_information(keywords)
                return render(request, 'summary.html', {'summary': summary})
    else:
        form = ImageUploadForm()
    return render(request, 'upload.html', {'form': form})
