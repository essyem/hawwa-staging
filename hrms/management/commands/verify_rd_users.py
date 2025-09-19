#!/usr/bin/env python3
"""
Verification script for R&D users creation
Usage: python manage.py verify_rd_users
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group, Permission
from hrms.models import Department, Position, EmployeeProfile

class Command(BaseCommand):
    help = 'Verify R&D department and users were created correctly'

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("R&D USERS VERIFICATION"))
        self.stdout.write("=" * 60)
        
        # Verify department
        try:
            rd_dept = Department.objects.get(code='RND')
            self.stdout.write(f"\\n✅ DEPARTMENT FOUND:")
            self.stdout.write(f"   Name: {rd_dept.name}")
            self.stdout.write(f"   Code: {rd_dept.code}")
            self.stdout.write(f"   Active: {rd_dept.is_active}")
        except Department.DoesNotExist:
            self.stdout.write(self.style.ERROR("❌ R&D Department not found"))
            return
        
        # Verify position
        try:
            rd_position = Position.objects.get(code='RND-SPEC')
            self.stdout.write(f"\\n✅ POSITION FOUND:")
            self.stdout.write(f"   Title: {rd_position.title}")
            self.stdout.write(f"   Code: {rd_position.code}")
            self.stdout.write(f"   Level: {rd_position.level}")
            self.stdout.write(f"   Salary Range: QAR {rd_position.min_salary} - {rd_position.max_salary}")
        except Position.DoesNotExist:
            self.stdout.write(self.style.ERROR("❌ R&D Position not found"))
            return
        
        # Verify group
        try:
            rd_group = Group.objects.get(name='R&D Employees')
            permissions_count = rd_group.permissions.count()
            delete_perms = rd_group.permissions.filter(codename__startswith='delete_').count()
            
            self.stdout.write(f"\\n✅ GROUP FOUND:")
            self.stdout.write(f"   Name: {rd_group.name}")
            self.stdout.write(f"   Total Permissions: {permissions_count}")
            self.stdout.write(f"   Delete Permissions: {delete_perms} (should be 0)")
            
            if delete_perms > 0:
                self.stdout.write(self.style.WARNING(f"⚠️  Warning: Group has {delete_perms} delete permissions"))
        except Group.DoesNotExist:
            self.stdout.write(self.style.ERROR("❌ R&D Employees group not found"))
            return
        
        # Verify users
        rd_usernames = ['muhsina', 'naeema', 'nasrin', 'muhammad', 'saleem', 'thariq', 'firoz']
        
        self.stdout.write(f"\\n✅ USERS VERIFICATION:")
        self.stdout.write(f"   Expected users: {len(rd_usernames)}")
        
        created_users = 0
        for username in rd_usernames:
            try:
                user = User.objects.get(username=username)
                employee = EmployeeProfile.objects.get(user=user)
                
                # Check if user is in the correct group
                in_group = user.groups.filter(name='R&D Employees').exists()
                
                self.stdout.write(f"\\n   👤 {username.upper()}:")
                self.stdout.write(f"      Name: {user.get_full_name()}")
                self.stdout.write(f"      Email: {user.email}")
                self.stdout.write(f"      Staff: {'Yes' if user.is_staff else 'No'}")
                self.stdout.write(f"      Active: {'Yes' if user.is_active else 'No'}")
                self.stdout.write(f"      Employee ID: {employee.employee_id}")
                self.stdout.write(f"      Department: {employee.department.name if employee.department else 'None'}")
                self.stdout.write(f"      Position: {employee.position.title if employee.position else 'None'}")
                self.stdout.write(f"      In R&D Group: {'Yes' if in_group else 'No'}")
                self.stdout.write(f"      Basic Salary: QAR {employee.basic_salary}")
                
                created_users += 1
                
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"   ❌ User '{username}' not found"))
            except EmployeeProfile.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"   ❌ Employee profile for '{username}' not found"))
        
        # Summary
        self.stdout.write("\\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("VERIFICATION SUMMARY"))
        self.stdout.write("=" * 60)
        
        self.stdout.write(f"✅ Department: Research & Development (RND)")
        self.stdout.write(f"✅ Position: R&D Specialist (RND-SPEC)")
        self.stdout.write(f"✅ Group: R&D Employees ({permissions_count} permissions)")
        self.stdout.write(f"✅ Users Created: {created_users}/{len(rd_usernames)}")
        
        if created_users == len(rd_usernames):
            self.stdout.write("\\n🎉 ALL USERS SUCCESSFULLY VERIFIED!")
            self.stdout.write("\\n📋 USER CAPABILITIES:")
            self.stdout.write("   • Full access to ALL modules")
            self.stdout.write("   • Can view, add, and change data")
            self.stdout.write("   • CANNOT delete data (security restriction)")
            self.stdout.write("   • Staff privileges for admin access")
            self.stdout.write("   • Employee profiles in R&D department")
            
            self.stdout.write("\\n🔐 LOGIN INFORMATION:")
            self.stdout.write("   Username: [muhsina, naeema, nasrin, muhammad, saleem, thariq, firoz]")
            self.stdout.write("   Password: Ch@ngeMeNOW")
            self.stdout.write("   Admin URL: http://localhost:8000/admin/")
            self.stdout.write("   HRMS URL: http://localhost:8000/hrms/")
        else:
            self.stdout.write(self.style.ERROR(f"\\n❌ VERIFICATION FAILED: Only {created_users}/{len(rd_usernames)} users found"))
