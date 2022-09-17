from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from ..models import Post, Group

User = get_user_model()


class PostURLTests(TestCase):
    """Тесты доступности страниц."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='name_test')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            pk=1,
            author=cls.user,
            text='Тестовый пост'
        )
        cls.url_names = {
            'posts/index.html': '/',
            'posts/group_list.html': '/group/test_slug/',
            'posts/profile.html': f'/profile/{PostURLTests.post.author}/',
            'posts/post_detail.html': f'/posts/{PostURLTests.post.pk}/',
        }

    def setUp(self):
        self.guest_client = Client()
        self.user = self.post.author
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_response_correct_not_logged_in(self):
        """Отображение страниц неавторизованным клиентам."""
        for template, address in PostURLTests.url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(HTTPStatus.OK, response.status_code)
                self.assertTemplateUsed(response, template)

    def test_response_correct_logged_in(self):
        """Отображение страниц авторизованным клиентам."""
        url_names_1 = {'posts/create_post.html': '/create/'}
        url_names_new = {**PostURLTests.url_names, **url_names_1}
        for template, address in url_names_new.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(HTTPStatus.OK, response.status_code)
                self.assertTemplateUsed(response, template)

    def test_edit_author_only(self):
        """Проверка редактирования и записи только у автора.
         Запрос на создание записи.
         """
        author_url = f'/posts/{PostURLTests.post.pk}/edit/'
        response = self.authorized_client.get(author_url)
        self.assertEqual(HTTPStatus.OK, response.status_code)

    def test_page_404(self):
        """Проверка запроса к несуществующей странице."""
        response = self.client.get('/undefined/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
