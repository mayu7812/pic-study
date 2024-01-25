from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from io import BytesIO
from myapp.forms import ImageUploadForm

class ImageUploadFormTest(TestCase):

    def test_valid_image(self):
        # 有効な画像を作成
        image_data = BytesIO()
        image = Image.new('RGB', size=(500, 500))
        image.save(image_data, format='JPEG')
        image_data.seek(0)
        uploaded_image = SimpleUploadedFile("valid_image.jpg", image_data.read())

        # 有効なデータでフォームを作成
        form_data = {'image': uploaded_image, 'category': 'nature'}
        form = ImageUploadForm(data=form_data)

        # フォームのバリデーションが成功することを確認
        self.assertTrue(form.is_valid())

    def test_invalid_image_format(self):
        # 無効な画像形式のファイルを作成
        image_data = BytesIO()
        invalid_image = Image.new('RGB', size=(500, 500))
        invalid_image.save(image_data, format='BMP')  # BMPは許可されていない形式
        image_data.seek(0)
        uploaded_image = SimpleUploadedFile("invalid_image.bmp", image_data.read())

        # 無効なデータでフォームを作成
        form_data = {'image': uploaded_image, 'category': 'people'}
        form = ImageUploadForm(data=form_data)

        # フォームのバリデーションが失敗することを確認
        self.assertFalse(form.is_valid())
        self.assertIn('image', form.errors)

    def test_large_file_size(self):
        # ファイルサイズが許容範囲を超えるファイルを作成
        image_data = BytesIO()
        large_image = Image.new('RGB', size=(100, 100))
        large_image.save(image_data, format='JPEG')
        image_data.seek(0)
        uploaded_image = SimpleUploadedFile("large_image.jpg", image_data.read())

        # データでフォームを作成
        form_data = {'image': uploaded_image, 'category': 'architecture'}
        form = ImageUploadForm(data=form_data)

        # フォームのバリデーションが失敗することを確認
        self.assertFalse(form.is_valid())
        self.assertIn('image', form.errors)

    # 他のテストケースも同様に追加できます。
