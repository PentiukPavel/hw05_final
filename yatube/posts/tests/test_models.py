from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        str_patterns = {
            self.group.title: str(self.group),
            self.post.text[:15]: str(self.post),
        }

        for obj, str_name in str_patterns.items():
            with self.subTest(obj=obj):
                self.assertEqual(obj, str_name)

    def test_verbose_name_post(self):
        """verbose_name в полях совпадает с ожидаемым для POST."""
        post = PostModelTest.post
        field_verboses = {
            'text': 'Текст Поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }

        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value
                )

    def test_verbose_name_group(self):
        """verbose_name в полях совпадает с ожидаемым для GROUP."""
        group = PostModelTest.group
        field_verboses = {
            'title': 'Заголовок группы',
            'slug': 'Адрес для страницы с группой',
            'description': 'Описание группы',
        }

        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    group._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_help_text_group(self):
        """help_text в полях совпадает с ожидаемым для GROUP."""
        group = PostModelTest.group
        field_help_texts = {
            'title': 'Введите заголовок группы',
            'description': 'Опишите группу',
        }

        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    group._meta.get_field(field).help_text,
                    expected_value
                )

    def test_help_text_post(self):
        """help_text в полях совпадает с ожидаемым для GROUP."""
        post = PostModelTest.post
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост',
        }

        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text,
                    expected_value
                )
