from django.contrib.auth import get_user_model
from django.test import TestCase
from ..models import Group, Post

User = get_user_model()

TEST_NUM = 15


class PostGroupModelTest(TestCase):
    """Тестирование __str__ моделей приложения."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Название группы',
            slug='test_slug1',
            description='Тестовая запись',
        )
        cls.post = Post.objects.create(
            text='Тестовая запись',
            author=User.objects.create_user(username='Mando'),
            group=cls.group
        )

    def test_post_text_field(self):
        """Правильное отображение значения поля __str__."""
        post = PostGroupModelTest.post
        expected_object_name = PostGroupModelTest.post.text[:TEST_NUM]
        self.assertEqual(expected_object_name, str(post))

    def test_group_title_field(self):
        """Правильное отображение значения поля __str__."""
        group = PostGroupModelTest.group
        expected_object_name = PostGroupModelTest.group.title
        self.assertEqual(expected_object_name, str(group))
