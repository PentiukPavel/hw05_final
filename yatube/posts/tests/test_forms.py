import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Comment, Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Vasya')
        cls.post = Post.objects.create(
            text='Пост до редактирования',
            author=cls.user,
        )
        cls.group = Group.objects.create(
            title='Та самая группа',
            description='Это та самая группа',
            slug='that_is_slug'
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorithed_client = Client()
        self.authorithed_client.force_login(self.user)

    def test_post_creation(self):
        """Post creation."""
        post_count = Post.objects.count()
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
        form_data = {
            'text': 'Тестовый пост',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorithed_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username},
            )
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertEqual(
            Post.objects.get(
                text='Тестовый пост'
            ).image,
            'posts/small.gif'
        )
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый пост',
                author=self.user.id,
                group=self.group.id,
                image='posts/small.gif'
            ).exists()
        )

    def test_post_edition(self):
        """Post edition."""
        self.authorithed_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}
            ),
            data={'text': 'Пост после редактирования'}
        )
        changed_post = Post.objects.get(id=self.post.id)
        self.assertEqual(changed_post.text, 'Пост после редактирования')


class CommentCreationTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='R2D2')
        cls.user2 = User.objects.create_user(username='Luke')
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user2,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_comment_creation(self):
        """Comment creation."""
        post = self.post
        count_comments = post.comments.count()
        form_data = {
            'text': 'Тестовый комментарий',
        }
        self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.id}
            ),
            data=form_data,
            follow=True
        )
        self.assertTrue(
            Comment.objects.filter(
                text='Тестовый комментарий',
                author=self.user.id,
                post=self.post.id,
            ).exists()
        )
        self.assertTrue(
            Comment.objects.filter(post=self.post.id).count(),
            count_comments + 1
        )
