from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_homepage(self):
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='Anonim')
        cls.user2 = User.objects.create_user(username='Vasya')
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

    def setUp(self) -> None:
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.user2)

    def test_urls_uses_correct_template(self):
        """Page templates test."""
        cache.clear()
        templates_url_name = {
            'posts/index.html': '/',
            'posts/group_list.html': f'/group/{self.group.slug}/',
            'posts/profile.html': f'/profile/{self.user.username}/',
            'posts/create_post.html': '/create/',
            'posts/post_detail.html': f'/posts/{self.post.id}/',
        }

        for template, address in templates_url_name.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_exist_at_desired_location_for_authorized_client(self):
        """URLs test for authorized user."""
        url_response_patterns = {
            '/': HTTPStatus.OK,
            f'/group/{self.group.slug}/': HTTPStatus.OK,
            f'/profile/{self.user.username}/': HTTPStatus.OK,
            '/create/': HTTPStatus.OK,
            f'/posts/{self.post.id}/': HTTPStatus.OK,
            f'/posts/{self.post.id}/edit/': HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
        }

        for url, enum_name in url_response_patterns.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, enum_name)

    def test_urls_exist_at_desired_location_for_guest_client(self):
        """URLs test for unauthorized user."""
        url_response_patterns = {
            '/': HTTPStatus.OK,
            f'/group/{self.group.slug}/': HTTPStatus.OK,
            f'/profile/{self.user.username}/': HTTPStatus.OK,
            '/create/': HTTPStatus.FOUND,
            f'/posts/{self.post.id}/': HTTPStatus.OK,
            f'/posts/{self.post.id}/edit/': HTTPStatus.FOUND,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
        }

        for url, status_code in url_response_patterns.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, status_code)

    def test_task_list_url_redirect_guest_client_on_admin_login(self):
        """Page /create/ redirect unauthorized user to login page."""
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/create/'
        )

    def test_task_list_url_redirect_authorized_client_on_post(self):
        """Page /posts/.../edit/ redirect user not author to post page."""
        response = self.authorized_client2.get(
            f'/posts/{self.post.id}/edit/',
            follow=True
        )
        self.assertRedirects(
            response, f'/posts/{self.post.id}/'
        )
