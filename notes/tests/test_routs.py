from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.reader = User.objects.create(username='Читатель')
        cls.note = Note.objects.create(
            title='Имя заметки',
            text='Текст заметки',
            slug='test_slug',
            author=cls.author
        )

    def test_home_page(self):
        """Главная страница доступна анонимному пользователю."""
        url = reverse('notes:home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_availability_for_user(self):
        """
        Аутентифицированному пользователю доступна страница со списком заметок
        notes/, страница успешного добавления заметки done/,
        страница добавления новой заметки add/.
        """
        urls = (
            'notes:list',
            'notes:success',
            'notes:add'
        )
        self.client.force_login(self.reader)
        for name in urls:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_availability_only_author(self):
        """
        Страницы отдельной заметки, удаления и редактирования заметки доступны
        только автору заметки. Если на эти страницы попытается зайти другой
        пользователь — вернётся ошибка 404.
        """
        users_statues = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        urls = (
            ('notes:detail', (self.note.slug,)),
            ('notes:delete', (self.note.slug,)),
            ('notes:edit', (self.note.slug,)),
        )
        for user, expected_status in users_statues:
            self.client.force_login(user)
            for name, arg in urls:
                with self.subTest(
                    user=user.username,
                    expected_status=expected_status,
                    name=name
                ):
                    url = reverse(name, args=arg)
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, expected_status)

    def test_redirect_annonymous_user_to_login_page(self):
        """
        При попытке перейти на страницу списка заметок, страницу успешного
        добавления записи, страницу добавления заметки, отдельной заметки,
        редактирования или удаления заметки анонимный пользователь
        перенаправляется на страницу логина.
        """
        urls = (
            ('notes:list', None),
            ('notes:success', None),
            ('notes:add', None),
            ('notes:detail', (self.note.slug,)),
            ('notes:delete', (self.note.slug,)),
            ('notes:edit', (self.note.slug,)),
        )
        login_url = reverse('users:login')
        for name, arg in urls:
            with self.subTest(name=name):
                url = reverse(name, args=arg)
                expected_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, expected_url)

    def test_pages_availability_for_everyone(self):
        """
        Страницы регистрации пользователей, входа в учётную запись и выхода
        из неё доступны всем пользователям.
        """
        urls = (
            'users:login',
            'users:signup',
            'users:logout',
        )
        for name in urls:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                if name == 'users:logout':
                    response = self.client.post(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
