from http import HTTPStatus
from pytils.translit import slugify

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note
from notes.forms import WARNING


User = get_user_model()


class TestNoteCreation(TestCase):

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
        cls.form_data = {
            'title': 'Новая заметка',
            'text': 'Текст заметки',
            'slug': 'new_slug'
        }

    def test_create_note_by_different_users(self):
        """
        Залогиненный пользователь может создать заметку,
        а анонимный — не может.
        """
        url = reverse('notes:add')
        response = self.client.post(url, data=self.form_data)
        login_url = reverse('users:login')
        expected_url = f'{login_url}?next={url}'
        self.assertRedirects(response, expected_url)
        self.assertEqual(Note.objects.count(), 1)
        self.client.force_login(self.author)
        response = self.client.post(url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 2)
        new_note = Note.objects.get(slug='new_slug')
        self.assertEqual(new_note.title, self.form_data['title'])
        self.assertEqual(new_note.text, self.form_data['text'])
        self.assertEqual(new_note.author, self.author)

    def test_slug_is_unique(self):
        """Невозможно создать две заметки с одинаковым slug."""
        self.client.force_login(self.author)
        url = reverse('notes:add')
        response = self.client.post(
            url,
            data={
                'title': 'Новая заметка',
                'text': 'Текст заметки',
                'slug': self.note.slug
            }
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        form = response.context['form']
        expected_error = self.note.slug + WARNING
        self.assertFormError(form, 'slug', expected_error)
        self.assertEqual(Note.objects.count(), 1)

    def test_empty_slug_automatic_create(self):
        """
        Если при создании заметки не заполнен slug, то он формируется
        автоматически, с помощью функции pytils.translit.slugify.
        """
        self.client.force_login(self.author)
        url = reverse('notes:add')
        new_data = {
            'title': 'Новая заметка',
            'text': 'Текст заметки',
            'slug': ''
        }
        response = self.client.post(
            url,
            data=new_data
        )
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 2)
        new_note = Note.objects.order_by('-id').first()
        expected_slug = slugify(new_data['title'])
        self.assertEqual(new_note.slug, expected_slug)

    def test_reader_cant_edit_or_delete_another_note(self):
        """Читатель не может изменить или удалить пост другого автора"""
        urls = ('notes:delete', 'notes:edit')
        self.client.force_login(self.reader)
        for name in urls:
            with self.subTest(name=name):
                url = reverse(name, args=(self.note.slug,))
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
                self.assertEqual(Note.objects.count(), 1)

    def test_author_can_edit_or_delete_another_note(self):
        """Автор может изменить или удалить пост другого автора"""
        self.client.force_login(self.author)
        edit_url = reverse('notes:edit', args=(self.note.slug,))
        new_data = {
            'title': 'Новый заголовок',
            'text': 'Новый текст'
        }
        response = self.client.post(edit_url, data=new_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, new_data['title'])

        delete_url = reverse('notes:delete', args=(self.note.slug,))
        response = self.client.post(delete_url)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 0)
