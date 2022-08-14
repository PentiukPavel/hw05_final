from django.test import Client, TestCase


class CoreTemplatesCheck(TestCase):
    def setUp(self):
        self.client = Client()
        self.templates_url_name = {
            'core/404.html': '/unexisting_page/',
        }

    def test_templates_for_url(self):
        for template, url in self.templates_url_name.items():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertTemplateUsed(response, template)
