# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.test import TestCase

class MovisterTestCase(TestCase):

class ModelTest(MovisterTestCase):


    def test_admin_list_delete(self):
        ''' Тест удаления списка через админку '''
        List(title='1', intro='2', author=self.user).save()

        self.assertEqual(List.objects.count(), 1)
        response = self.client.post(reverse('admin:movister_list_delete', args=(1,)),  {'post': 'yes'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(List.objects.count(), 0)

    def test_admin_text_delete(self):
        ''' Тест удаления текста через админку '''
        Text(title='1', text='2', author=self.user).save()

        self.assertEqual(Text.objects.count(), 1)
        response = self.client.post(reverse('admin:movister_text_delete', args=(1,)),  {'post': 'yes'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Text.objects.count(), 0)