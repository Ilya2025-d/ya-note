from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note
from notes.forms import NoteForm

User = get_user_model()


class TestContent(TestCase):

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

    def test_personal_note_in_object_list(self):
        """
        Отдельная заметка передаётся на страницу со списком заметок в списке
        object_list в словаре context.
        """
        self.client.force_login(self.author)
        url = reverse('notes:list')
        response = self.client.get(url)
        object_list = response.context['object_list']
        self.assertIn(self.note, object_list)

    def test_note_list_user_not_in_note_list_another_user(self):
        """
        В список заметок одного пользователя не попадают
        заметки другого пользователя.
        """
        self.client.force_login(self.reader)
        url = reverse('notes:list')
        response = self.client.get(url)
        object_list = response.context['object_list']
        self.assertNotIn(self.note, object_list)

    def test_form_on_create_and_delet_pages(self):
        """На страницы создания и редактирования заметки передаются формы."""
        self.client.force_login(self.author)
        urls = (
            ('notes:add', None),
            ('notes:edit', (self.note.slug,)),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], NoteForm)
