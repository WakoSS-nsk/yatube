import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostFormTests(TestCase):
    """Форма создания и редактирования поста."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.user = User.objects.create_user(username='mando')
        cls.group = Group.objects.create(
            title='test group',
            slug='test_slug',
            description='test description'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_user_can_create_post(self):
        """Пользователь может создать пост."""
        count_posts = Post.objects.count()
        form_data = {
            'text': 'new post',
            'group': PostFormTests.group.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        post = Post.objects.first()
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group, PostFormTests.group)
        self.assertEqual(Post.objects.count(), count_posts + 1)
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': self.user}
        ))

    def test_unauthorized_cannot_create_post(self):
        """Неавторизованный не может создавать посты."""
        count_posts = Post.objects.count()
        response = self.client.post(
            reverse('posts:post_create'),
            data={'text': 'Test post', 'group': PostFormTests.group.id},
        )
        login_url = reverse('users:login')
        new_post_url = reverse('posts:post_create')
        target_url = f'{login_url}?next={new_post_url}'
        self.assertRedirects(response, target_url)
        self.assertEqual(Post.objects.count(), count_posts)

    def test_authorized_edit_post(self):
        """авторизованный пользователь может редактировать пост."""
        form_data = {
            'text': 'new post',
            'group': PostFormTests.group.id
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        post_2 = Post.objects.get(id=PostFormTests.group.id)
        self.client.get(f'/posts/{post_2.id}/edit/')
        form_data = {
            'text': 'edited',
            'group': PostFormTests.group.id
        }
        response_edit = self.authorized_client.post(
            reverse('posts:post_edit', args=(post_2.id,)),
            data=form_data,
            follow=True,
        )
        post_2 = Post.objects.get(id=PostFormTests.group.id)
        self.assertEqual(response_edit.status_code, HTTPStatus.OK)
        self.assertEqual(post_2.text, 'edited')
