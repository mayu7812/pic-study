from PIL import Image
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class ImageUploadForm(forms.Form):
    image = forms.ImageField()

    ALLOWED_IMAGE_FORMATS = ['jpeg', 'png', 'gif']
    MAX_FILE_SIZE_MB = 10
    MIN_ASPECT_RATIO = 0.5
    MAX_ASPECT_RATIO = 2.0
    MIN_RESOLUTION = 100 * 100
    MAX_RESOLUTION = 2000 * 2000

    ALLOWED_CATEGORIES = ['nature', 'people', 'architecture']  # 仮のカテゴリリスト

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            main, sub = image.content_type.split('/')
            if not (main == 'image' and sub.lower() in self.ALLOWED_IMAGE_FORMATS):
                raise ValidationError(_('{}形式の画像を使用してください。').format(', '.join(self.ALLOWED_IMAGE_FORMATS)))

            max_size_bytes = self.MAX_FILE_SIZE_MB * 1024 * 1024
            if image.size > max_size_bytes:
                raise ValidationError(_('ファイルサイズは{}MB以下にしてください。').format(self.MAX_FILE_SIZE_MB))

            pil_image = Image.open(image)
            width, height = pil_image.size
            aspect_ratio = width / height
            resolution = width * height

            if aspect_ratio < self.MIN_ASPECT_RATIO or aspect_ratio > self.MAX_ASPECT_RATIO:
                raise ValidationError(_('画像のアスペクト比は{}から{}の間にしてください。').format(self.MIN_ASPECT_RATIO, self.MAX_ASPECT_RATIO))

            if resolution < self.MIN_RESOLUTION or resolution > self.MAX_RESOLUTION:
                raise ValidationError(_('画像の解像度は{}から{}の間にしてください。').format(self.MIN_RESOLUTION, self.MAX_RESOLUTION))

            # 新しい機能: 特定のカテゴリに分類されている場合の処理
            category = self.cleaned_data.get('category')
            if category and category.lower() not in self.ALLOWED_CATEGORIES:
                raise ValidationError(_('このカテゴリの画像はアップロードできません。'))
        return image