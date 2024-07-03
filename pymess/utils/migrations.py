import codecs
import os
from typing import Any

from chamber.shortcuts import change_and_save

from pymess.config import settings

__all__ = [
    "change_and_save",
    "get_email_template_body_from_file",
    "SyncEmailTemplates",
]


def get_email_template_body_from_file(email_template_slug, locale):
    base_dir = settings.EMAIL_HTML_DATA_DIRECTORY
    if locale:
        base_dir = os.path.join(settings.EMAIL_HTML_DATA_DIRECTORY, locale)
    with codecs.open(os.path.join(
            base_dir,
            '{}.html'.format(email_template_slug)), 'r', encoding='utf-8-sig') as file:
        return file.read()


class SyncEmailTemplates:

    def __init__(self, template_slugs=None, locale=None):
        self.template_slugs = template_slugs
        self.locale = locale

    def __call__(self, apps, schema_editor):
        email_template_class = apps.get_model(*settings.EMAIL_TEMPLATE_MODEL.split('.'))
        email_template_qs = email_template_class.objects.all()
        if self.template_slugs:
            email_template_qs = email_template_qs.filter(slug__in=self.template_slugs, locale=self.locale)
        email_templates_found = list(email_template_qs)
        if self.template_slugs:
            email_templates_not_found = set(self.template_slugs) - {t.slug for t in email_templates_found}
            assert not email_templates_not_found, f"Email templates {email_templates_not_found} were not found."
        for email_template in email_templates_found:
            email_template.body = get_email_template_body_from_file(email_template.slug, self.locale)
        email_template_class.objects.bulk_update(email_templates_found, ['body'])
