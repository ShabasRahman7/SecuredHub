"""
Management command to load built-in compliance standards.

Usage:
    python manage.py load_builtin_standards
    python manage.py load_builtin_standards --force  # Reload even if exists
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from standards.models import ComplianceStandard


class Command(BaseCommand):
    help = 'Load built-in compliance standards from fixture'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force reload even if standards already exist',
        )
    
    def handle(self, *args, **options):
        force = options.get('force', False)
        
        # Check if built-in standards already exist
        existing_count = ComplianceStandard.objects.filter(is_builtin=True).count()
        
        if existing_count > 0 and not force:
            self.stdout.write(
                self.style.WARNING(
                    f'Built-in standards already exist ({existing_count} found). '
                    'Use --force to reload.'
                )
            )
            return
        
        if force and existing_count > 0:
            # Delete existing built-in standards (cascade will remove rules)
            deleted, _ = ComplianceStandard.objects.filter(is_builtin=True).delete()
            self.stdout.write(
                self.style.WARNING(f'Deleted {deleted} existing objects.')
            )
        
        # Load the fixture
        try:
            call_command(
                'loaddata',
                'standards/fixtures/builtin_standards.json',
                verbosity=0
            )
            
            # Verify loading
            new_count = ComplianceStandard.objects.filter(is_builtin=True).count()
            rules_count = sum(
                s.rules.count() 
                for s in ComplianceStandard.objects.filter(is_builtin=True)
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully loaded {new_count} built-in standard(s) '
                    f'with {rules_count} rule(s).'
                )
            )
            
            # List what was loaded
            for standard in ComplianceStandard.objects.filter(is_builtin=True):
                self.stdout.write(
                    f'  - {standard.name} (v{standard.version}): '
                    f'{standard.rules.count()} rules, '
                    f'total weight: {standard.total_weight}'
                )
                
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f'Failed to load standards: {str(e)}')
            )
            raise
