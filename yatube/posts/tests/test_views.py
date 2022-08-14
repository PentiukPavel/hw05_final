import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Follow, Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='Anonim')
        cls.group = Group.objects.create(
            id=10,
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            id=1,
            text='Тестовый пост',
            author=cls.user,
            group=cls.group,
            image=uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        cache.clear()
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_posts',
                kwargs={'slug': 'test-slug'},
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': 'Anonim'},
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': 1},
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': 1}
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_detail_page_show_correct_context(self):
        """Правильный контекст страницы поста."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': 1},
            )
        )
        post = response.context['post']
        self.post_text = post.text
        self.post_image = post.image
        self.assertEqual(self.post_text, 'Тестовый пост')
        self.assertEqual(self.post_image, 'posts/small.gif')

    def test_index_page_show_correct_context(self):
        """Правильный контекст индексной страницы."""
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        post = response.context['page_obj'][0]
        self.post_text = post.text
        self.post_id = post.id
        self.post_image = post.image
        self.assertEqual(self.post_text, 'Тестовый пост')
        self.assertEqual(self.post_id, 1)
        self.assertEqual(self.post_image, 'posts/small.gif')

    def test_group_list_page_show_correct_context(self):
        """Правильный контекст страницы группы."""
        response = self.authorized_client.get(reverse(
            'posts:group_posts',
            kwargs={'slug': 'test-slug'}
            )
        )
        group = response.context['page_obj'][0]
        self.group_text = group.text
        self.group_id = group.id
        self.group_group = group.group.id
        self.group_image = group.image
        self.assertEqual(self.group_text, 'Тестовый пост')
        self.assertEqual(self.group_id, 1)
        self.assertEqual(self.group_group, 10)
        self.assertEqual(self.group_image, 'posts/small.gif')

    def test_profile_page_show_correct_context(self):
        """Правильный контекст страницы автора."""
        response = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': 'Anonim'}
            )
        )
        profile = response.context['page_obj'][0]
        posts_quantity = response.context['posts_quantity']
        author = response.context['author']
        self.profile_text = profile.text
        self.profile_image = profile.image
        self.profile_id = profile.id
        self.profile_group = profile.group.id
        self.posts_quantity = posts_quantity
        self.author = author.id
        self.assertEqual(self.profile_text, 'Тестовый пост')
        self.assertEqual(self.profile_id, 1)
        self.assertEqual(self.profile_group, 10)
        self.assertEqual(self.posts_quantity, 1)
        self.assertEqual(self.author, 1)
        self.assertEqual(self.profile_image, 'posts/small.gif')

    def test_post_create_page_show_correct_context(self):
        """Правильный контекст страницы создания поста."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Контекст страницы редактирования поста."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': 1}
            )
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='Vasya')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.posts = Post.objects.bulk_create(
            [Post(
                text=f'Тестовый пост {number}',
                author=cls.user,
                group=cls.group,
            ) for number in range(1, 12)])

    def setUp(self):
        self.client = Client()

    def test_first_index_page_contains_ten_records(self):
        """Паджинатор индексной страницы. Записи на первой странице."""
        cache.clear()
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_index_page_contains_one_record(self):
        """Паджинатор индексной страницы. Записи на второй странице."""
        cache.clear()
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_first_group_list_page_contains_ten_records(self):
        """Паджинатор страницы группы. Записи на первой странице."""
        response = self.client.get(
            reverse(
                'posts:group_posts',
                kwargs={'slug': 'test-slug'}
            )
        )
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_group_list_page_contains_one_record(self):
        """Паджинатор страницы группы. Записи на второй странице."""
        response = self.client.get(
            reverse(
                'posts:group_posts',
                kwargs={'slug': 'test-slug'}
            ) + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_first_profile_page_contains_ten_records(self):
        """Паджинатор страницы автора. Записи на первой странице."""
        cache.clear()
        response = self.client.get(
            reverse(
                'posts:profile',
                kwargs={'username': 'Vasya'}
            )
        )
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_profile_page_contains_one_record(self):
        """Паджинатор страницы автора. Записи на второй странице."""
        cache.clear()
        response = self.client.get(
            reverse(
                'posts:profile',
                kwargs={'username': 'Vasya'}
            ) + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), 1)


class PostCreateTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Anonim')
        cls.group = Group.objects.create(
            id=2,
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post_quantuty = Group.objects.create(
            id=10,
            title='Тестовая группа 2',
            slug='test-slug2',
            description='Тестовое описание',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_post_creation(self):
        """Пост появляется на главной странице."""
        self.authorized_client.post(
            reverse('posts:post_create'),
            {'text': 'Тестовый пост', 'group': 10}
        )
        response = self.authorized_client.get(reverse('posts:index'))
        post = response.context['page_obj'][0]
        self.post_text = post.text
        self.post_group = post.group.id
        self.assertEqual(self.post_text, 'Тестовый пост')
        self.assertEqual(self.post_group, 10)

    def test_post_in_ceratain_group(self):
        """Пост появляется на странице его группы."""
        self.authorized_client.post(
            reverse('posts:post_create'),
            {'text': 'Тестовый пост', 'group': 10}
        )
        response = self.authorized_client.get(
            reverse('posts:group_posts', kwargs={'slug': 'test-slug2'})
        )
        post = response.context['page_obj'][0]
        self.group_text = post.text
        response2 = self.authorized_client.get(
            reverse('posts:group_posts', kwargs={'slug': 'test-slug'})
        )
        self.post_quantuty = len(response2.context['page_obj'])
        self.assertEqual(self.group_text, 'Тестовый пост')
        self.assertEqual(self.post_quantuty, 0)


class CommentCreationTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='R2D2')
        cls.post = Post.objects.create(
            id=78,
            text='Тестовый пост',
            author=cls.user
        )

    def setUp(self):
        self.client = Client()

    def test_comment_creates_only_by_authorized_client(self):
        """Создание комментария только авторизованным пользователем"""
        post = self.post
        count_comments = post.comments.count()
        form_data = {
            'text': 'Тестовый комментарий',
        }
        self.client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': 78}
            ),
            data=form_data,
            follow=True
        )
        self.assertFalse(
            Comment.objects.filter(
                text='Тестовый комментарий',
                author=self.user.id,
                post=post.id,
            ).exists()
        )
        self.assertFalse(
            Comment.objects.filter(post=post.id).count(),
            count_comments + 1
        )


class IndexPageCacheTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='Vasya')
        cls.post = Post.objects.create(
            id=111,
            text='Тестовый тест',
            author=cls.user
        )
        cls.post2 = Post.objects.create(
            id=222,
            text='Новый пост',
            author=cls.user
        )

    def setUp(self) -> None:
        self.client = Client()
        self.client.force_login(self.user)

    def test_index_page_cache(self):
        """Кеишрование индексной страницы"""
        cache.clear()
        self.client.get(reverse('posts:index'))
        post_to_eliminate = Post.objects.get(id=111)
        post_to_eliminate.delete()
        response = self.client.get(reverse('posts:index'))
        self.assertTrue(bytes('Тестовый тест', 'utf-8') in response.content)
        cache.clear()
        response2 = self.client.get(reverse('posts:index'))
        self.assertFalse(bytes('Тестовый тест', 'utf-8') in response2.content)


class SubscriptionTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_vasya = User.objects.create_user(username='Vasya')
        cls.user_petya = User.objects.create_user(username='Petya')
        cls.user_sasha = User.objects.create_user(username='Sasha')
        cls.subscription = Follow.objects.create(
            user=cls.user_sasha,
            author=cls.user_petya
        )

    def setUp(self):
        self.client_vasya = Client()
        self.client_vasya.force_login(self.user_vasya)
        self.client_petya = Client()
        self.client_petya.force_login(self.user_petya)
        self.client_sasha = Client()
        self.client_sasha.force_login(self.user_sasha)

    def test_authorized_client_subscriptions_making(self):
        """Подписки авторизованного пользователя"""
        self.client_vasya.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': 'Petya'}
            )
        )
        subscription = Follow.objects.filter(
            user=self.user_vasya,
            author=self.user_petya
        )
        self.assertTrue(subscription.exists())

    def test_authorized_client_subscriptions_deny(self):
        """Отказ от подписки"""
        self.client_petya.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': 'Vasya'}
            )
        )
        self.client_petya.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': 'Vasya'}
            )
        )
        subscription = Follow.objects.filter(
            user=self.user_petya,
            author=self.user_vasya
        )
        self.assertFalse(subscription.exists())

    def test_new_post_for_followers(self):
        """Новый пост в ленте у подписчиков"""
        self.client_petya.post(
            reverse('posts:post_create'),
            data={'text': 'Тестовый пост', }
        )
        response_sasha = self.client_sasha.get(
            reverse('posts:follow_index')
        )
        response_vasya = self.client_vasya.get(
            reverse('posts:follow_index')
        )
        self.assertTrue(
            bytes('Тестовый пост', 'utf-8') in response_sasha.content
        )
        self.assertFalse(
            bytes('Тестовый пост', 'utf-8') in response_vasya.content
        )
