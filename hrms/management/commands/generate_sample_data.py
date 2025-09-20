import random
from datetime import date, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from faker import Faker
from hrms.models import (
    Company, Department, Position, Grade, EmployeeProfile,
    TrainingCategory, TrainingProgram, LeaveType, 
    LeaveBalance, PayrollPeriod, PayrollItem
)

class Command(BaseCommand):
    help = 'Generates comprehensive sample data for HRMS system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--employees',
            type=int,
            default=50,
            help='Number of employees to create (default: 50)',
        )

    def handle(self, *args, **options):
        fake = Faker()
        Faker.seed(42)  # For consistent results
        
        num_employees = options['employees']
        
        self.stdout.write(self.style.SUCCESS('🚀 Starting HRMS sample data generation...'))
        
        # 1. Create Company
        self.create_company(fake)
        
        # 2. Create Departments
        self.create_departments(fake)
        
        # 3. Create Grades
        self.create_grades()
        
        # 4. Create Positions
        self.create_positions(fake)
        
        # 5. Create Leave Types
        self.create_leave_types()
        
        # 6. Create Training Categories
        self.create_training_categories(fake)
        
        # 7. Create Employees
        self.create_employees(fake, num_employees)
        
        # 8. Create Training Programs
        self.create_training_programs(fake)
        
        # 9. Create Payroll Data
        self.create_payroll_data(fake)
        
        self.stdout.write(self.style.SUCCESS(f'✅ Successfully generated comprehensive HRMS data with {num_employees} employees!'))

    def create_company(self, fake):
        if Company.objects.exists():
            self.stdout.write(self.style.WARNING('Company data already exists, skipping...'))
            return
            
        company = Company.objects.create(
            name='IFCC Qatar',
            legal_name='IFCC Qatar LLC',
            registration_number='CR-2020-001234',
            tax_number='TAX-QA-987654321',
            address='Building 123, West Bay Area, Doha, Qatar',
            country='QA',
            phone='+974-4444-5555',
            email='hello@hawwawellness.com',
            website='https://ifccqatar.com',
            established_date=fake.date_between(start_date='-10y', end_date='-2y')
        )
        self.stdout.write(self.style.SUCCESS(f'📢 Created company: {company.name}'))

    def create_departments(self, fake):
        if Department.objects.exists():
            self.stdout.write(self.style.WARNING('Department data already exists, skipping...'))
            return
            
        departments_data = [
            ('EXEC', 'Executive', 'Senior leadership and strategic direction'),
            ('HR', 'Human Resources', 'Employee relations, recruitment, and development'),
            ('FIN', 'Finance & Accounting', 'Financial planning, accounting, and analysis'),
            ('IT', 'Information Technology', 'Software development and IT infrastructure'),
            ('OPS', 'Operations', 'Business operations and process management'),
            ('MKT', 'Marketing', 'Brand management and marketing campaigns'),
            ('SALES', 'Sales', 'Revenue generation and customer acquisition'),
            ('SUPP', 'Customer Support', 'Customer service and technical support'),
            ('RND', 'Research & Development', 'Innovation and product development'),
            ('LEGAL', 'Legal & Compliance', 'Legal affairs and regulatory compliance'),
            ('ADMIN', 'Administration', 'General administration and facilities'),
        ]
        
        for code, name, description in departments_data:
            department = Department.objects.create(
                name=name,
                code=code,
                description=description,
                budget=fake.pydecimal(left_digits=7, right_digits=2, positive=True),
                is_active=True
            )
            self.stdout.write(self.style.SUCCESS(f'🏢 Created department: {department.name}'))

    def create_grades(self):
        if Grade.objects.exists():
            self.stdout.write(self.style.WARNING('Grade data already exists, skipping...'))
            return
            
        grades_data = [
            ('G1', 'Graduate Trainee', 25000, 35000, 8.0),
            ('G2', 'Junior Professional', 35000, 50000, 7.0),
            ('G3', 'Professional', 50000, 70000, 6.0),
            ('G4', 'Senior Professional', 70000, 95000, 5.5),
            ('G5', 'Team Leader', 95000, 120000, 5.0),
            ('G6', 'Manager', 120000, 150000, 4.5),
            ('G7', 'Senior Manager', 150000, 200000, 4.0),
            ('G8', 'Director', 200000, 300000, 3.5),
            ('G9', 'Senior Director', 300000, 400000, 3.0),
            ('G10', 'Executive', 400000, 600000, 2.5),
        ]
        
        for code, name, min_sal, max_sal, increment in grades_data:
            grade = Grade.objects.create(
                name=name,
                code=code,
                min_salary=Decimal(str(min_sal)),
                max_salary=Decimal(str(max_sal)),
                annual_increment_percentage=Decimal(str(increment)),
                benefits_package=f'Standard benefits package for {name} level',
                is_active=True
            )
            self.stdout.write(self.style.SUCCESS(f'📊 Created grade: {grade.name}'))

    def create_positions(self, fake):
        if Position.objects.exists():
            self.stdout.write(self.style.WARNING('Position data already exists, skipping...'))
            return
            
        positions_data = [
            # Executive
            ('CEO001', 'Chief Executive Officer', 'EXEC', 'executive', 'G10'),
            ('CTO001', 'Chief Technology Officer', 'IT', 'executive', 'G9'),
            ('CFO001', 'Chief Financial Officer', 'FIN', 'executive', 'G9'),
            ('CHRO001', 'Chief Human Resources Officer', 'HR', 'executive', 'G9'),
            
            # Directors
            ('DIR001', 'Director of Operations', 'OPS', 'director', 'G8'),
            ('DIR002', 'Director of Sales', 'SALES', 'director', 'G8'),
            ('DIR003', 'Director of Marketing', 'MKT', 'director', 'G8'),
            
            # Managers
            ('MGR001', 'IT Manager', 'IT', 'manager', 'G6'),
            ('MGR002', 'HR Manager', 'HR', 'manager', 'G6'),
            ('MGR003', 'Finance Manager', 'FIN', 'manager', 'G6'),
            ('MGR004', 'Operations Manager', 'OPS', 'manager', 'G6'),
            ('MGR005', 'Customer Support Manager', 'SUPP', 'manager', 'G6'),
            
            # Team Leaders
            ('TL001', 'Development Team Lead', 'IT', 'lead', 'G5'),
            ('TL002', 'QA Team Lead', 'IT', 'lead', 'G5'),
            ('TL003', 'Sales Team Lead', 'SALES', 'lead', 'G5'),
            ('TL004', 'Support Team Lead', 'SUPP', 'lead', 'G5'),
            
            # Senior Professionals
            ('SP001', 'Senior Software Engineer', 'IT', 'senior', 'G4'),
            ('SP002', 'Senior Business Analyst', 'OPS', 'senior', 'G4'),
            ('SP003', 'Senior Accountant', 'FIN', 'senior', 'G4'),
            ('SP004', 'Senior HR Specialist', 'HR', 'senior', 'G4'),
            ('SP005', 'Senior Marketing Specialist', 'MKT', 'senior', 'G4'),
            
            # Professionals
            ('PR001', 'Software Engineer', 'IT', 'mid', 'G3'),
            ('PR002', 'Business Analyst', 'OPS', 'mid', 'G3'),
            ('PR003', 'Accountant', 'FIN', 'mid', 'G3'),
            ('PR004', 'HR Specialist', 'HR', 'mid', 'G3'),
            ('PR005', 'Marketing Specialist', 'MKT', 'mid', 'G3'),
            ('PR006', 'Sales Executive', 'SALES', 'mid', 'G3'),
            ('PR007', 'Customer Support Executive', 'SUPP', 'mid', 'G3'),
            
            # Junior Professionals
            ('JP001', 'Junior Software Engineer', 'IT', 'junior', 'G2'),
            ('JP002', 'Junior Analyst', 'OPS', 'junior', 'G2'),
            ('JP003', 'Junior Accountant', 'FIN', 'junior', 'G2'),
            ('JP004', 'Junior HR Associate', 'HR', 'junior', 'G2'),
            ('JP005', 'Marketing Associate', 'MKT', 'junior', 'G2'),
            ('JP006', 'Sales Associate', 'SALES', 'junior', 'G2'),
            
            # Entry Level
            ('EN001', 'Graduate Trainee - IT', 'IT', 'entry', 'G1'),
            ('EN002', 'Graduate Trainee - Finance', 'FIN', 'entry', 'G1'),
            ('EN003', 'Graduate Trainee - HR', 'HR', 'entry', 'G1'),
            ('EN004', 'Administrative Assistant', 'ADMIN', 'entry', 'G1'),
            ('EN005', 'Customer Service Representative', 'SUPP', 'entry', 'G1'),
        ]
        
        for code, title, dept_code, level, grade_code in positions_data:
            department = Department.objects.get(code=dept_code)
            grade = Grade.objects.get(code=grade_code)
            
            position = Position.objects.create(
                title=title,
                code=code,
                department=department,
                level=level,
                min_salary=grade.min_salary,
                max_salary=grade.max_salary,
                description=f'<p>Responsible for {title.lower()} duties in the {department.name} department.</p>',
                requirements=f'<p>Requirements for {title} position include relevant education and experience.</p>',
                responsibilities=f'<p>Key responsibilities include {title.lower()} activities and team collaboration.</p>',
                is_active=True
            )
            self.stdout.write(self.style.SUCCESS(f'💼 Created position: {position.title}'))

    def create_leave_types(self):
        if LeaveType.objects.exists():
            self.stdout.write(self.style.WARNING('Leave types already exist, skipping...'))
            return
            
        leave_types_data = [
            ('AL', 'Annual Leave', 21, 5, True, True, 30, 7),
            ('SL', 'Sick Leave', 7, 0, True, False, 7, 0),
            ('ML', 'Maternity Leave', 45, 0, True, True, 45, 30),
            ('PL', 'Paternity Leave', 3, 0, True, True, 3, 7),
            ('EL', 'Emergency Leave', 2, 0, True, True, 2, 0),
            ('UL', 'Unpaid Leave', 0, 0, False, True, 10, 7),
            ('CL', 'Compassionate Leave', 3, 0, True, True, 3, 0),
            ('HL', 'Hajj Leave', 15, 0, True, True, 15, 60),
        ]
        
        for code, name, days, carry, is_paid, requires_approval, max_consecutive, notice_days in leave_types_data:
            leave_type = LeaveType.objects.create(
                name=name,
                code=code,
                days_allowed_per_year=days,
                carry_forward_days=carry,
                is_paid=is_paid,
                requires_approval=requires_approval,
                max_consecutive_days=max_consecutive,
                notice_days_required=notice_days,
                is_active=True
            )
            self.stdout.write(self.style.SUCCESS(f'🏖️ Created leave type: {leave_type.name}'))

    def create_training_categories(self, fake):
        if TrainingCategory.objects.exists():
            self.stdout.write(self.style.WARNING('Training categories already exist, skipping...'))
            return
            
        # Training Categories
        categories_data = [
            ('Technical Skills', 'Programming, software development, and technical competencies'),
            ('Leadership & Management', 'Leadership development and management skills'),
            ('Communication Skills', 'Verbal, written, and presentation skills'),
            ('Professional Development', 'Career development and professional skills'),
            ('Compliance & Safety', 'Regulatory compliance and workplace safety'),
            ('Customer Service', 'Customer interaction and service excellence'),
            ('Project Management', 'Project planning, execution, and management'),
            ('Financial Management', 'Financial analysis, budgeting, and accounting'),
            ('Digital Literacy', 'Digital tools and modern workplace technologies'),
            ('Quality Management', 'Quality assurance and process improvement'),
        ]
        
        for name, description in categories_data:
            category = TrainingCategory.objects.create(
                name=name,
                description=description,
                is_active=True
            )
            self.stdout.write(self.style.SUCCESS(f'📚 Created training category: {category.name}'))

    def create_employees(self, fake, num_employees):
        if EmployeeProfile.objects.count() >= num_employees:
            self.stdout.write(self.style.WARNING(f'Already have {EmployeeProfile.objects.count()} employees, skipping...'))
            return
            
        positions = list(Position.objects.all())
        departments = list(Department.objects.all())
        grades = list(Grade.objects.all())
        leave_types = list(LeaveType.objects.all())
        
        for i in range(num_employees):
            # Create user
            first_name = fake.first_name()
            last_name = fake.last_name()
            username = f"{first_name.lower()}.{last_name.lower()}{i}"[:30]
            email = f"{username}@ifccqatar.com"
            
            user = User.objects.create_user(
                username=username,
                email=email,
                password='password123',
                first_name=first_name,
                last_name=last_name
            )
            
            # Select position and department
            position = fake.random_element(positions)
            department = position.department
            grade = fake.random_element(grades)
            
            # Generate employee data
            hire_date = fake.date_between(start_date='-5y', end_date='today')
            salary = fake.pydecimal(
                left_digits=6, 
                right_digits=2, 
                positive=True,
                min_value=grade.min_salary,
                max_value=grade.max_salary
            )
            
            # Create employee profile
            employee = EmployeeProfile.objects.create(
                user=user,
                employee_id=f'EMP{str(i+1).zfill(4)}',
                date_of_birth=fake.date_of_birth(minimum_age=22, maximum_age=65),
                place_of_birth=fake.city(),
                nationality='Qatari' if fake.boolean(chance_of_getting_true=30) else fake.country(),
                gender=fake.random_element(['male', 'female']),
                marital_status=fake.random_element(['single', 'married', 'divorced']),
                blood_group=fake.random_element(['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']),
                personal_email=fake.email(),
                phone_number=fake.phone_number()[:30],
                emergency_contact_name=fake.name(),
                emergency_contact_phone=fake.phone_number()[:30],
                emergency_contact_relationship=fake.random_element(['spouse', 'parent', 'sibling', 'friend']),
                current_address=fake.address(),
                permanent_address=fake.address(),
                department=department,
                position=position,
                grade=grade,
                employment_type=fake.random_element(['permanent', 'contract', 'temporary']),
                work_location='Doha Office',
                hire_date=hire_date,
                basic_salary=salary,
                housing_allowance=salary * Decimal('0.3'),
                transport_allowance=Decimal('1500'),
                other_allowances=Decimal('500'),
                status='active',
                created_by=user
            )
            
            # Create leave balances
            self.create_leave_balances(employee, leave_types)
            
            if i % 10 == 0:
                self.stdout.write(self.style.SUCCESS(f'👥 Created {i+1} employees...'))
        
        self.stdout.write(self.style.SUCCESS(f'✅ Created {num_employees} employees successfully!'))

    def create_leave_balances(self, employee, leave_types):
        current_year = timezone.now().year
        for leave_type in leave_types:
            if leave_type.days_allowed_per_year > 0:
                LeaveBalance.objects.create(
                    employee=employee,
                    leave_type=leave_type,
                    year=current_year,
                    entitled_days=Decimal(str(leave_type.days_allowed_per_year)),
                    used_days=Decimal(str(random.randint(0, leave_type.days_allowed_per_year // 3))),
                    pending_days=Decimal('0')
                )

    def create_training_programs(self, fake):
        if TrainingProgram.objects.exists():
            self.stdout.write(self.style.WARNING('Training programs already exist, skipping...'))
            return
            
        categories = list(TrainingCategory.objects.all())
        if not categories:
            self.stdout.write(self.style.WARNING('No training categories found, skipping training programs...'))
            return
        
        programs_data = [
            ('LEAD101', 'Leadership Fundamentals', 'Leadership & Management', 'classroom', 'beginner', 16),
            ('TECH201', 'Advanced Python Programming', 'Technical Skills', 'online', 'advanced', 24),
            ('COMM101', 'Effective Communication', 'Communication Skills', 'workshop', 'beginner', 8),
            ('PROJ301', 'Project Management Professional', 'Project Management', 'certification', 'advanced', 40),
            ('SAFE101', 'Workplace Safety Training', 'Compliance & Safety', 'classroom', 'beginner', 4),
            ('CUST201', 'Customer Service Excellence', 'Customer Service', 'interactive', 'intermediate', 12),
            ('FIN301', 'Financial Analysis & Reporting', 'Financial Management', 'online', 'advanced', 20),
            ('DIGI101', 'Digital Workplace Skills', 'Digital Literacy', 'online', 'beginner', 8),
            ('QUAL201', 'Quality Management Systems', 'Quality Management', 'classroom', 'intermediate', 16),
            ('MGMT401', 'Strategic Management', 'Leadership & Management', 'seminar', 'expert', 32),
        ]
        
        # Get an admin user for created_by field
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.first()
        
        for code, title, cat_name, training_type, level, hours in programs_data:
            try:
                category = TrainingCategory.objects.get(name=cat_name)
                
                program = TrainingProgram.objects.create(
                    title=title,
                    code=code,
                    category=category,
                    description=f'<p>Comprehensive {title.lower()} program designed to enhance professional skills.</p>',
                    objectives=f'<p>Upon completion, participants will have mastered key concepts in {title.lower()}.</p>',
                    prerequisites=f'<p>Basic understanding of {cat_name.lower()} recommended.</p>',
                    duration_hours=hours,
                    max_participants=20,
                    training_type=training_type,
                    level=level,
                    cost_per_participant=Decimal(str(hours * 50)),  # QAR 50 per hour
                    materials='Training materials and resources included',
                    is_mandatory=fake.boolean(chance_of_getting_true=20),
                    is_active=True,
                    created_by=admin_user
                )
                self.stdout.write(self.style.SUCCESS(f'🎓 Created training program: {program.title}'))
            except TrainingCategory.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Training category "{cat_name}" not found, skipping program "{title}"'))

    def create_payroll_data(self, fake):
        if PayrollPeriod.objects.exists():
            self.stdout.write(self.style.WARNING('Payroll data already exists, skipping...'))
            return
            
        # Create payroll periods for the last 3 months
        current_date = timezone.now().date()
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.first()
        
        for i in range(3):
            start_date = current_date.replace(day=1) - timedelta(days=i*30)
            end_date = (start_date.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
            pay_date = end_date + timedelta(days=5)
            
            period = PayrollPeriod.objects.create(
                name=f"{start_date.strftime('%B %Y')} Payroll",
                start_date=start_date,
                end_date=end_date,
                pay_date=pay_date,
                status='paid' if i > 0 else 'approved',
                created_by=admin_user
            )
            
            # Create payroll items for all employees
            employees = EmployeeProfile.objects.all()[:20]  # Limit to first 20 for demo
            for employee in employees:
                # Calculate totals
                basic = employee.basic_salary
                housing = employee.housing_allowance
                transport = employee.transport_allowance
                overtime = Decimal(str(fake.random_int(min=0, max=2000)))
                bonus = Decimal(str(fake.random_int(min=0, max=5000))) if fake.boolean(chance_of_getting_true=30) else Decimal('0')
                
                gross = basic + housing + transport + overtime + bonus
                tax = basic * Decimal('0.05')  # 5% tax
                insurance = Decimal('500')
                total_deductions = tax + insurance
                net = gross - total_deductions
                
                PayrollItem.objects.create(
                    employee=employee,
                    payroll_period=period,
                    basic_salary=basic,
                    housing_allowance=housing,
                    transport_allowance=transport,
                    overtime_amount=overtime,
                    bonus=bonus,
                    tax_deduction=tax,
                    insurance_deduction=insurance,
                    gross_salary=gross,
                    total_deductions=total_deductions,
                    net_salary=net,
                    status='paid' if i > 0 else 'approved'
                )
            
            self.stdout.write(self.style.SUCCESS(f'💰 Created payroll period: {period.name}'))

        self.stdout.write(self.style.SUCCESS('💼 Payroll data generation completed!'))