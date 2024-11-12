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

def get_email_template_body_from_file(email_template_slug, locale, variant):
    base_dir = settings.EMAIL_HTML_DATA_DIRECTORY
    if locale:
        base_dir = os.path.join(base_dir, locale)
    filename = f'{email_template_slug}_{variant}' if variant else email_template_slug
    file_path = os.path.join(base_dir, f'{filename}.html')
    with codecs.open(file_path, 'r', encoding='utf-8-sig') as file:
        return file.read()



class SyncEmailTemplates:

    def __init__(self, template_slugs=None, locale=None, variant=None, unlock=True):
        self.template_slugs = template_slugs
        self.locale = locale
        self.variant = variant
        self.unlock = unlock
        
    def __call__(self, apps, schema_editor):
        email_template_class = apps.get_model(*settings.EMAIL_TEMPLATE_MODEL.split('.'))
        email_template_qs = email_template_class.objects.all()
        
        filters = {}
        if self.template_slugs:
            filters['slug__in'] = self.template_slugs
        if self.locale:
            filters['locale'] = self.locale
        if self.variant:
            filters['variant'] = self.variant
        
        email_template_qs = email_template_qs.filter(**filters)
        email_templates_found = list(email_template_qs)
        
        if self.template_slugs:
            email_templates_not_found = set(self.template_slugs) - {t.slug for t in email_templates_found}
            assert not email_templates_not_found, f"Email templates {email_templates_not_found} were not found."
        for email_template in email_templates_found:
            email_template.body = get_email_template_body_from_file(email_template.slug, self.locale, self.variant)
            email_template.is_locked = not self.unlock
        email_template_class.objects.bulk_update(email_templates_found, ['body', 'is_locked'])
