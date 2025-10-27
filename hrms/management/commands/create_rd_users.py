#!/usr/bin/env python3
"""
Django Management Command to create users with full privileges
Usage: python manage.py create_rd_users
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from hrms.models import Department, Position, EmployeeProfile, Company
from datetime import date
import uuid

class Command(BaseCommand):
    help = 'Create R&D department and users with full privileges except delete'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating anything',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # User data
        users_data = [
            {'username': 'muhsina', 'first_name': 'Muhsina', 'last_name': 'Ahmed'},
            {'username': 'naeema', 'first_name': 'Naeema', 'last_name': 'Ali'},
            {'username': 'nasrin', 'first_name': 'Nasrin', 'last_name': 'Khan'},
            {'username': 'muhammad', 'first_name': 'Muhammad', 'last_name': 'Hassan'},
            {'username': 'saleem', 'first_name': 'Saleem', 'last_name': 'Ahmed'},
            {'username': 'thariq', 'first_name': 'Thariq', 'last_name': 'Rahman'},
            {'username': 'firoz', 'first_name': 'Firoz', 'last_name': 'Shah'},
        ]
        
        password = "Ch@ngeMeNOW"
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
            self.show_plan(users_data, password)
            return
        
        try:
            with transaction.atomic():
                # Step 1: Create or get R&D Department
                rd_dept, created = self.create_rd_department()
                
                # Step 2: Create or get R&D Position
                rd_position = self.create_rd_position(rd_dept)
                
                # Step 3: Create or get the group with permissions
                rd_group = self.create_rd_group()
                
                # Step 4: Create users and employee profiles
                created_users = []
                for user_data in users_data:
                    user, employee = self.create_user_and_employee(
                        user_data, password, rd_dept, rd_position, rd_group
                    )
                    created_users.append((user, employee))
                
                # Step 5: Summary
                self.print_summary(rd_dept, rd_position, rd_group, created_users)
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating users: {str(e)}')
            )
            raise
    
    def show_plan(self, users_data, password):
        self.stdout.write("\\n" + "="*60)
        self.stdout.write(self.style.SUCCESS("EXECUTION PLAN"))
        self.stdout.write("="*60)
        
        self.stdout.write("\\n1. CREATE R&D DEPARTMENT:")
        self.stdout.write("   - Name: Research & Development")
        self.stdout.write("   - Code: RND")
        self.stdout.write("   - Description: Research and Development Department")
        
        self.stdout.write("\\n2. CREATE R&D POSITION:")
        self.stdout.write("   - Title: R&D Specialist")
        self.stdout.write("   - Department: Research & Development")
        
        self.stdout.write("\\n3. CREATE R&D EMPLOYEE GROUP:")
        self.stdout.write("   - Name: R&D Employees")
        self.stdout.write("   - Permissions: All modules EXCEPT delete permissions")
        
        self.stdout.write("\\n4. CREATE USERS:")
        for user_data in users_data:
            self.stdout.write(f"   - Username: {user_data['username']}")
            self.stdout.write(f"     Name: {user_data['first_name']} {user_data['last_name']}")
            self.stdout.write(f"     Password: {password}")
            self.stdout.write(f"     Department: R&D")
            self.stdout.write(f"     Position: R&D Specialist")
            self.stdout.write(f"     Employee ID: RND-{user_data['username'].upper()}")
            self.stdout.write("")
        
        self.stdout.write("\\nRun without --dry-run to execute the plan.")
    
    def create_rd_department(self):
        dept, created = Department.objects.get_or_create(
            code='RND',
            defaults={
                'name': 'Research & Development',
                'description': 'Research and Development Department focused on innovation and technology advancement',
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Created department: {dept.name}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'📁 Department already exists: {dept.name}')
            )
        
        return dept, created
    
    def create_rd_position(self, department):
        position, created = Position.objects.get_or_create(
            title='R&D Specialist',
            department=department,
            defaults={
                'code': 'RND-SPEC',
                'level': 'mid',
                'min_salary': 6000.00,
                'max_salary': 12000.00,
                'description': 'Research and Development Specialist responsible for innovation projects',
                'requirements': 'Bachelor degree in relevant field, 2+ years experience in R&D',
                'responsibilities': 'Conduct research, develop new products, analyze market trends, collaborate with teams',
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Created position: {position.title}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'💼 Position already exists: {position.title}')
            )
        
        return position
    
    def create_rd_group(self):
        group, created = Group.objects.get_or_create(
            name='R&D Employees'
        )
        
        if created or not group.permissions.exists():
            # Get all permissions except delete permissions
            all_permissions = Permission.objects.exclude(
                codename__startswith='delete_'
            ).exclude(
                codename__in=['delete_user', 'delete_group', 'delete_permission']
            )
            
            group.permissions.set(all_permissions)
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Created group: {group.name}')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Updated permissions for group: {group.name}')
                )
            
            self.stdout.write(
                self.style.SUCCESS(f'   📋 Added {all_permissions.count()} permissions (excluding delete)')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'👥 Group already exists with permissions: {group.name}')
            )
        
        return group
    
    def create_user_and_employee(self, user_data, password, department, position, group):
        username = user_data['username']
        User = get_user_model()

        # Create or get user using email as username field for custom User model
        email = f"{username}@company.com"
        # Provide a default user_type for R&D users; use 'ADMIN' to grant access to staff pages
        defaults = {
            'first_name': user_data['first_name'],
            'last_name': user_data['last_name'],
            'email': email,
            'is_staff': True,  # Give staff privileges
            'is_active': True,
            # If the custom User model requires 'user_type', default to 'ADMIN'
        }
        # If user_type is a required field on the custom User model, set it safely
        try:
            # don't assume attribute exists; set if allowed
            defaults.update({'user_type': 'ADMIN'})
        except Exception:
            pass

        user, user_created = User.objects.get_or_create(
            email=email,
            defaults=defaults,
        )
        
        if user_created:
            user.set_password(password)
            # set an unusable username attr if the model has it but it's not used
            if not getattr(user, 'username', None):
                try:
                    setattr(user, 'username', username)
                except Exception:
                    pass
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f'✅ Created user: {email}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'👤 User already exists: {email}')
            )
        
        # Add user to group
        user.groups.add(group)
        
        # Create or get employee profile
        employee_id = f"RND-{username.upper()}"
        
        employee, emp_created = EmployeeProfile.objects.get_or_create(
            user=user,
            defaults={
                'employee_id': employee_id,
                'department': department,
                'position': position,
                'hire_date': date.today(),
                'status': 'active',
                'employment_type': 'permanent',
                'basic_salary': 8000.00,  # Default salary
                'phone_number': f"+974-5555-{username[:4]}",
                'nationality': 'Qatari',
                'gender': 'other'
            }
        )
        
        if emp_created:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Created employee profile: {employee_id}')
            )
        else:
            # Update department and position if employee exists
            employee.department = department
            employee.position = position
            employee.save()
            self.stdout.write(
                self.style.WARNING(f'👷 Employee profile already exists, updated dept/position: {employee_id}')
            )
        
        return user, employee
    
    def print_summary(self, department, position, group, created_users):
        self.stdout.write("\\n" + "="*60)
        self.stdout.write(self.style.SUCCESS("CREATION SUMMARY"))
        self.stdout.write("="*60)
        
        self.stdout.write(f"\\n🏢 DEPARTMENT: {department.name} ({department.code})")
        self.stdout.write(f"💼 POSITION: {position.title}")
        self.stdout.write(f"👥 GROUP: {group.name} ({group.permissions.count()} permissions)")
        
        self.stdout.write(f"\\n👤 CREATED USERS ({len(created_users)}):")
        for user, employee in created_users:
            self.stdout.write(f"   • {user.username} → {employee.employee_id}")
            self.stdout.write(f"     Name: {user.get_full_name()}")
            self.stdout.write(f"     Email: {user.email}")
            self.stdout.write(f"     Staff: {'Yes' if user.is_staff else 'No'}")
            self.stdout.write(f"     Groups: {', '.join([g.name for g in user.groups.all()])}")
            self.stdout.write("")
        
        self.stdout.write("🎉 ALL USERS CREATED SUCCESSFULLY!")
        self.stdout.write("\\nℹ️  LOGIN CREDENTIALS:")
        self.stdout.write("   Password for all users: Ch@ngeMeNOW")
        self.stdout.write("   Users should change password on first login")
        
        self.stdout.write("\\n🔗 ACCESS URLS:")
        self.stdout.write("   • Admin: http://localhost:8000/admin/")
        self.stdout.write("   • HRMS: http://localhost:8000/hrms/")
        self.stdout.write("   • Frontend: http://localhost:8000/")
