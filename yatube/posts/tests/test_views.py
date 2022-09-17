from django import forms
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Follow, Post

User = get_user_model()

PAGE_NUM = 10
PAGE_NUM_TOTAL = 13
ZERO = 0
ONE = 1


class PostPagesTests(TestCase):
    """Проверка шаблонов на правильное содержание."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='mando')
        cls.group = Group.objects.create(
            title='Заголовок для 1 группы',
            slug='test_slug1',
            description='Тестовая запись 1',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=PostPagesTests.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Тестовая запись 2',
            author=PostPagesTests.user,
            group=PostPagesTests.group,
            image=PostPagesTests.uploaded,
        )
        cls.index = reverse('posts:main_page')
        cls.profile = reverse('posts:profile',
                              kwargs={'username': cls.user})
        cls.post_detail = reverse('posts:post_detail',
                                  kwargs={'post_id': cls.post.id})
        cls.post_edit = reverse('posts:post_edit',
                                kwargs={'post_id': cls.post.id})
        cls.group_list = reverse('posts:group_list',
                                 kwargs={'slug': cls.group.slug})
        cls.create = reverse('posts:post_create')
        cls.main = reverse('posts:main_page')
        cls.template_url = (
            'posts:main_page',
            'posts:group_list',
            'posts:profile',
        )
        cls.follow = Follow.objects.create(
            user=cls.user,
            author=cls.post.author
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.user)
        self.client_auth_follower = Client()
        self.client_auth_following = Client()
        self.user_follower = User.objects.create_user(username='follower')
        self.user_following = User.objects.create_user(username='following')
        self.client_auth_follower.force_login(self.user_follower)
        self.client_auth_following.force_login(self.user_following)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            PostPagesTests.index: 'posts/index.html',
            PostPagesTests.profile: 'posts/profile.html',
            PostPagesTests.post_detail: 'posts/post_detail.html',
            PostPagesTests.group_list: 'posts/group_list.html',
            PostPagesTests.create: 'posts/create_post.html',
        }

        for reverse_name, template in templates_page_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_pages_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(PostPagesTests.index)
        post = response.context["page_obj"][ZERO]
        self.assertEqual(post.text, PostPagesTests.post.text)
        self.assertEqual(post.author, PostPagesTests.user)
        self.assertEqual(post.group, PostPagesTests.group)

    def test_group_posts_show_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        response = self.authorized_client.get(PostPagesTests.group_list)
        group = response.context['group']
        self.assertEqual(group.title, PostPagesTests.group.title)
        self.assertEqual(group.slug, PostPagesTests.group.slug)

    def test_post_profile_show_correct_context(self):
        """Шаблон post_profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(PostPagesTests.profile)
        first_object = response.context['page_obj'][ZERO]
        post_text_0 = first_object.text
        self.assertEqual(response.context['author'].username,
                         self.user.username)
        self.assertEqual(post_text_0, PostPagesTests.post.text)

    def test_post_detail_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(PostPagesTests.post_detail)
        self.assertEqual(response.context['post'].text, self.post.text)
        self.assertEqual(response.context['post'].author, self.user)
        self.assertEqual(response.context['post'].group, self.post.group)

    def test_post_create_show_correct_context(self):
        """Шаблон create_post с правильным контекстом."""
        response = self.authorized_client.get(PostPagesTests.create)
        form_fields = {
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(PostPagesTests.post_edit)
        form_fields = {
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_pages_contain_correct_number_of_posts(self):
        """Тестирование паджинатора."""
        posts = [
            Post(
                text=f'Тестовый пост {num}',
                author=PostPagesTests.user,
                group=PostPagesTests.group
            ) for num in range(1, PAGE_NUM_TOTAL)
        ]
        Post.objects.bulk_create(posts)
        pages = {
            1: PAGE_NUM,
            2: PAGE_NUM_TOTAL - PAGE_NUM,
        }

        list_urls = (
            PostPagesTests.index,
            PostPagesTests.group_list,
            PostPagesTests.profile,
        )
        for url in list_urls:
            for page, count in pages.items():
                response = self.client.get(url, {'page': page})
                self.assertEqual(
                    len(response.context.get('page_obj').object_list), count
                )

    def test_cache_index(self):
        """Тест кэширования страницы index.html"""
        first_state = self.authorized_client.get(PostPagesTests.main)
        post_1 = Post.objects.get(pk=1)
        post_1.text = 'Измененный текст'
        post_1.save()
        second_state = self.authorized_client.get(PostPagesTests.main)
        self.assertEqual(first_state.content, second_state.content)
        cache.clear()
        third_state = self.authorized_client.get(PostPagesTests.main)
        self.assertNotEqual(first_state.content, third_state.content)

    def test_add_comment(self):
        """Проверка работы комментариев."""
        comment_url = reverse(
            'posts:add_comment', kwargs={'post_id': PostPagesTests.post.id}
        )
        expected_result = f'{reverse("users:login")}?next='
        response = self.client.get(comment_url)
        self.assertRedirects(response, expected_result + comment_url)

    def test_post_with_picture(self):
        """Проверим, что картинка появляется на всех нужных страницах."""
        urls = (PostPagesTests.group_list,
                PostPagesTests.profile,
                PostPagesTests.main,
                )
        form_data = {
            'text': 'Пост с картинкой',
            'group': PostPagesTests.group.id,
            'image': PostPagesTests.uploaded
        }
        response_1 = self.authorized_client.get(
            PostPagesTests.post_detail,
            data=form_data,
            follow=True)
        self.assertEqual(PostPagesTests.post.image,
                         response_1.context['post'].image)
        self.assertContains(response_1, '<img')
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(
                    url,
                    data=form_data,
                    follow=True)
                self.assertEqual(PostPagesTests.post.image,
                                 response.context['page_obj'][ZERO].image)

    def test_follow(self):
        """Проверка функции подписки на автора."""
        followers = Follow.objects.all().count()
        self.client_auth_follower.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user.username}))
        self.assertTrue(Follow.objects.filter(
            user=self.user_follower,
            author=PostPagesTests.user).exists())
        self.assertEqual(Follow.objects.count(), followers + ONE)

    def test_unfollow(self):
        """Проверка функции отмены подписки на автора."""
        self.client_auth_follower.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user.username}))
        followers = Follow.objects.count()
        self.client_auth_follower.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.user.username})
        )
        self.assertFalse(Follow.objects.filter(
            user=self.user_follower,
            author=PostPagesTests.user).exists())
        self.assertEqual(Follow.objects.count(), followers - ONE)

    def test_subscription_feed(self):
        """Запись появляется в ленте подписчиков."""
        follow_post = Post.objects.create(
            author=self.user_following,
            text='Тестовая запись'
        )
        Follow.objects.create(user=self.user_follower,
                              author=self.user_following)
        response = self.client_auth_follower.get('/follow/')
        post_text_0 = response.context["page_obj"][ZERO].text
        self.assertEqual(post_text_0, follow_post.text)
        response = self.client_auth_following.get('/follow/')
        self.assertNotContains(response, follow_post.text)
