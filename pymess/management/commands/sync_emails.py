import codecs
import os

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand

from pymess.config import get_email_template_model, settings


class Command(BaseCommand):
    """
    Command to synchronize e-mail bodies from directory.
    Default templates remain the same. Variant B templates have the '_B' suffix.
    """

    def _sync_for_locale(self, base_directory, locale, variant):
        locale_directory = os.path.join(base_directory, locale) if locale else base_directory

        files_with_email_html_body = [
            filename for filename in os.listdir(locale_directory) if filename.endswith('.html')
        ]
        for filename in files_with_email_html_body:
            slug, _ = filename.rsplit('_' if variant else '.html', 1)
            try:
                template_obj = get_email_template_model().objects.get(slug=slug, locale=locale, variant=variant)
                with codecs.open(os.path.join(locale_directory, filename), 'r', encoding='utf-8-sig') as file:
                    template_obj.change_and_save(body=file.read())
            except ObjectDoesNotExist:
                if verbosity > 0:
                    self.stderr.write('Template model with slug "{}" does not exists'.format(filename[:-5]))
        if verbosity > 0:
            self.stdout.write(
                self.style.SUCCESS('Synced "{}" e-mail templates'.format(len(files_with_email_html_body)))
            )

    def handle(self, *args, **options):
        verbosity = int(options.get('verbosity'))
        variant = str(options.get('variant'))
        if verbosity > 0:
            self.stdout.write('Syncing e-mails')

        directory = os.path.join(settings.EMAIL_HTML_DATA_DIRECTORY)
        # All dirs in the root directory represent a locale.
        # e.g., `$EMAIL_HTML_DATA_DIRECTORY/cs/`, `$EMAIL_HTML_DATA_DIRECTORY/sk/`.
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isdir(file_path):
                self._sync_for_locale(directory, filename, variant)

        # The `$EMAIL_HTML_DATA_DIRECTORY/` directory itself represents the locale of None value.
        self._sync_for_locale(directory, None, variant)
