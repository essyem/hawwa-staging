from django.core.management.base import BaseCommand
from hrms.models import EducationLevel, DocumentType

class Command(BaseCommand):
    help = 'Populate initial data for education levels and document types'

    def handle(self, *args, **options):
        self.stdout.write('Populating Education Levels and Document Types...')
        
        # Create Education Levels
        education_levels = [
            ('High School', 'high_school', 1),
            ('Higher Secondary', 'higher_secondary', 2),
            ('Diploma', 'diploma', 3),
            ('Bachelor Degree', 'bachelor', 4),
            ('Master Degree', 'master', 5),
            ('PhD', 'phd', 6),
            ('Professional Certification', 'professional', 7),
            ('Vocational Training', 'vocational', 3),
            ('Other', 'other', 8),
        ]
        
        for name, code, level_order in education_levels:
            education_level, created = EducationLevel.objects.get_or_create(
                code=code,
                defaults={'name': name, 'level_order': level_order}
            )
            if created:
                self.stdout.write(f'Created Education Level: {education_level}')
            else:
                self.stdout.write(f'Education Level already exists: {education_level}')
        
        # Create Document Types
        document_types = [
            # Identity Documents
            ('Qatar ID', 'identity', True, True),
            ('Passport', 'identity', True, True),
            ('National ID', 'identity', False, True),
            ('Driving License', 'identity', False, True),
            
            # Educational Documents
            ('Educational Certificate', 'education', False, False),
            ('University Degree', 'education', False, False),
            ('Professional Certificate', 'education', False, False),
            ('Training Certificate', 'education', False, False),
            ('Transcript', 'education', False, False),
            
            # Employment Documents
            ('Employment Contract', 'employment', True, False),
            ('Job Offer Letter', 'employment', False, False),
            ('Previous Employment Certificate', 'employment', False, False),
            ('No Objection Certificate (NOC)', 'employment', False, True),
            ('Work Permit', 'employment', False, True),
            
            # Visa & Immigration
            ('Residence Permit (RP)', 'visa', True, True),
            ('Entry Visa', 'visa', False, True),
            ('Exit Permit', 'visa', False, True),
            ('Family Visa', 'visa', False, True),
            
            # Medical Documents
            ('Medical Certificate', 'medical', False, True),
            ('Vaccination Certificate', 'medical', False, True),
            ('Health Insurance Card', 'medical', False, True),
            ('Medical Test Results', 'medical', False, False),
            
            # Other Documents
            ('Bank Account Details', 'other', False, False),
            ('Emergency Contact Form', 'other', False, False),
            ('Photo', 'other', False, False),
            ('CV/Resume', 'other', False, False),
        ]
        
        for name, category, is_required, has_expiry in document_types:
            doc_type, created = DocumentType.objects.get_or_create(
                name=name,
                defaults={
                    'category': category,
                    'is_required': is_required,
                    'has_expiry': has_expiry
                }
            )
            if created:
                self.stdout.write(f'Created Document Type: {doc_type}')
            else:
                self.stdout.write(f'Document Type already exists: {doc_type}')
        
        self.stdout.write(self.style.SUCCESS('Initial data population completed!'))
