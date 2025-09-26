from django.core.management.base import BaseCommand
from django.template.loader import get_template
from django.template import TemplateSyntaxError
import os
from collections import defaultdict


class Command(BaseCommand):
    help = 'Compile all templates under project templates/ directories to detect syntax errors.'

    def handle(self, *args, **options):
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
        errors = defaultdict(list)
        count = 0

        for dirpath, dirnames, filenames in os.walk(root):
            for f in filenames:
                if not f.endswith('.html'):
                    continue
                path = os.path.join(dirpath, f)
                parts = path.split(os.sep)
                if 'templates' in parts:
                    idx = len(parts) - 1 - parts[::-1].index('templates')
                    tmpl_name = os.sep.join(parts[idx+1:])
                else:
                    continue
                count += 1
                try:
                    get_template(tmpl_name)
                    self.stdout.write(self.style.SUCCESS(f'OK: {tmpl_name}'))
                except Exception as e:
                    etype = type(e).__name__
                    errors[etype].append((tmpl_name, str(e)))
                    self.stdout.write(self.style.ERROR(f'ERROR: {tmpl_name} -> {etype}: {e}'))

        self.stdout.write('')
        self.stdout.write(f'Templates scanned: {count}')
        total_errors = sum(len(v) for v in errors.values())
        self.stdout.write(f'Errors: {total_errors}')
        if total_errors:
            for etype, items in errors.items():
                self.stdout.write(f'\n{etype}: {len(items)}')
                for tmpl, msg in items[:50]:
                    self.stdout.write(f' - {tmpl}: {msg}')
            raise SystemExit(1)
        else:
            self.stdout.write(self.style.SUCCESS('All templates compiled successfully.'))
