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
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
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
        """Templates for pages test."""
        cache.clear()
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_posts',
                kwargs={'slug': self.group.slug},
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username},
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id},
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_detail_page_show_correct_context(self):
        """Context test for post page."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id},
            )
        )
        post = response.context['post']
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.image, 'posts/small.gif')

    def test_index_page_show_correct_context(self):
        """Context test for index page."""
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        post = response.context['page_obj'][0]
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.id, self.post.id)
        self.assertEqual(post.image, 'posts/small.gif')

    def test_group_list_page_show_correct_context(self):
        """Context test for group list page."""
        response = self.authorized_client.get(
            reverse(
                'posts:group_posts',
                kwargs={'slug': self.group.slug}
            )
        )
        post = response.context['page_obj'][0]
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.id, self.post.id)
        self.assertEqual(post.group.id, self.group.id)
        self.assertEqual(post.image, 'posts/small.gif')

    def test_profile_page_show_correct_context(self):
        """Context test for profile page."""
        response = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            )
        )
        profile = response.context['page_obj'][0]
        posts_quantity = response.context['posts_quantity']
        author = response.context['author']
        self.assertEqual(profile.text, self.post.text)
        self.assertEqual(profile.id, self.post.id)
        self.assertEqual(profile.group.id, self.group.id)
        self.assertEqual(posts_quantity, 1)
        self.assertEqual(author.id, self.user.id)
        self.assertEqual(profile.image, 'posts/small.gif')

    def test_post_create_page_show_correct_context(self):
        """Context test for post creation page."""
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
        """Context test for post edition page."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}
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
        """Index page paginator. First page."""
        cache.clear()
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_index_page_contains_one_record(self):
        """Index page paginator. Second page"""
        cache.clear()
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_first_group_list_page_contains_ten_records(self):
        """Group page paginator. First page."""
        response = self.client.get(
            reverse(
                'posts:group_posts',
                kwargs={'slug': self.group.slug}
            )
        )
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_group_list_page_contains_one_record(self):
        """Group page paginator. Second page."""
        response = self.client.get(
            reverse(
                'posts:group_posts',
                kwargs={'slug': self.group.slug}
            ) + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_first_profile_page_contains_ten_records(self):
        """Author page paginator. First page."""
        response = self.client.get(
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            )
        )
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_profile_page_contains_one_record(self):
        """Author page paginator. Second page."""
        response = self.client.get(
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            ) + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), 1)


class PostCreateTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Anonim')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug2',
            description='Тестовое описание',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_post_creation(self):
        """Post appears at index page."""
        self.authorized_client.post(
            reverse('posts:post_create'),
            {'text': 'Тестовый пост', 'group': self.group2.id}
        )
        response = self.authorized_client.get(reverse('posts:index'))
        post = response.context['page_obj'][0]
        self.assertEqual(post.text, 'Тестовый пост')
        self.assertEqual(post.group.id, self.group2.id)

    def test_post_in_ceratain_group(self):
        """Post appears at the page of it's group, not at the page of others."""
        self.authorized_client.post(
            reverse('posts:post_create'),
            {'text': 'Тестовый пост', 'group': self.group2.id}
        )
        response = self.authorized_client.get(
            reverse('posts:group_posts', kwargs={'slug': self.group2.slug})
        )
        post = response.context['page_obj'][0]
        response2 = self.authorized_client.get(
            reverse('posts:group_posts', kwargs={'slug': self.group.slug})
        )
        post_quantity = len(response2.context['page_obj'])
        self.assertEqual(post.text, 'Тестовый пост')
        self.assertEqual(post_quantity, 0)


class CommentCreationTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='R2D2')
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user
        )

    def setUp(self):
        self.client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_unauthorized_user_cant_publish_comment(self):
        """Unauthorized user can't add a comment."""
        post = self.post
        count_comments = post.comments.count()
        form_data = {
            'text': 'Тестовый комментарий',
        }
        self.client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.id}
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


    def test_redirect_after_post_creation(self):
        """Redirection after comment creation test."""
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.id}
            ),
            data={'text': 'Тестовый комментарий'},
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id},
            )
        )


class IndexPageCacheTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='Vasya')
        cls.post = Post.objects.create(
            text='Тестовый тест',
            author=cls.user
        )

    def setUp(self) -> None:
        self.client = Client()
        self.client.force_login(self.user)

    def test_index_page_cache(self):
        """Index page cache test."""
        cache.clear()
        self.client.get(reverse('posts:index'))
        post_to_eliminate = Post.objects.get(id=self.post.id)
        post_to_eliminate.delete()
        response = self.client.get(reverse('posts:index'))
        self.assertTrue(bytes(self.post.text, 'utf-8') in response.content)
        cache.clear()
        response2 = self.client.get(reverse('posts:index'))
        self.assertFalse(bytes(self.post.text, 'utf-8') in response2.content)


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
        """Authorized client's subscription test."""
        self.client_vasya.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user_petya.username}
            )
        )
        subscription = Follow.objects.filter(
            user=self.user_vasya,
            author=self.user_petya
        )
        self.assertTrue(subscription.exists())

    def test_authorized_client_subscriptions_deny(self):
        """Subscription rejection."""
        self.client_petya.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user_vasya.username}
            )
        )
        self.client_petya.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.user_vasya.username}
            )
        )
        subscription = Follow.objects.filter(
            user=self.user_petya,
            author=self.user_vasya
        )
        self.assertFalse(subscription.exists())

    def test_new_post_for_followers(self):
        """Post appears in followers set."""
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
