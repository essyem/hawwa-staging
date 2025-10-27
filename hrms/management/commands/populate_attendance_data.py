from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta, time
from hrms.models import (
    WorkSchedule, EmployeeSchedule, Attendance, EmployeeProfile
)
from decimal import Decimal
import random

class Command(BaseCommand):
    help = 'Populate attendance system with sample data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days of attendance data to create (default: 30)'
        )

    def handle(self, *args, **options):
        days = options['days']
        self.stdout.write(f"Creating attendance data for {days} days...")
        
        # Create Work Schedules
        self.create_work_schedules()
        
        # Assign schedules to employees
        self.assign_employee_schedules()
        
        # Create attendance records
        self.create_attendance_records(days)
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully populated attendance data for {days} days!')
        )

    def create_work_schedules(self):
        """Create sample work schedules"""
        schedules = [
            {
                'name': 'Standard Office Hours',
                'schedule_type': 'fixed',
                'description': 'Monday to Friday, 9 AM to 6 PM',
                'start_time': time(9, 0),
                'end_time': time(18, 0),
                'work_days': [1, 2, 3, 4, 5],  # Monday to Friday
                'weekly_hours': Decimal('40.00'),
                'overtime_after_hours': Decimal('8.00'),
                'overtime_rate': Decimal('1.50'),
                'late_grace_minutes': 15,
                'early_departure_minutes': 15,
            },
            {
                'name': 'Early Shift',
                'schedule_type': 'shift',
                'description': 'Early morning shift, 7 AM to 4 PM',
                'start_time': time(7, 0),
                'end_time': time(16, 0),
                'work_days': [1, 2, 3, 4, 5],
                'weekly_hours': Decimal('40.00'),
                'overtime_after_hours': Decimal('8.00'),
                'overtime_rate': Decimal('1.50'),
                'late_grace_minutes': 10,
                'early_departure_minutes': 10,
            },
            {
                'name': 'Flexible Hours',
                'schedule_type': 'flexible',
                'description': 'Flexible working hours with core time',
                'start_time': time(8, 0),
                'end_time': time(17, 0),
                'work_days': [1, 2, 3, 4, 5],
                'weekly_hours': Decimal('40.00'),
                'overtime_after_hours': Decimal('8.00'),
                'overtime_rate': Decimal('1.50'),
                'late_grace_minutes': 30,
                'early_departure_minutes': 30,
            },
            {
                'name': 'Remote Work Schedule',
                'schedule_type': 'remote',
                'description': 'Full remote work schedule',
                'start_time': time(9, 0),
                'end_time': time(18, 0),
                'work_days': [1, 2, 3, 4, 5],
                'weekly_hours': Decimal('40.00'),
                'overtime_after_hours': Decimal('8.00'),
                'overtime_rate': Decimal('1.50'),
                'late_grace_minutes': 30,
                'early_departure_minutes': 30,
            }
        ]
        
        for schedule_data in schedules:
            schedule, created = WorkSchedule.objects.get_or_create(
                name=schedule_data['name'],
                defaults=schedule_data
            )
            if created:
                self.stdout.write(f"Created work schedule: {schedule.name}")

    def assign_employee_schedules(self):
        """Assign schedules to employees"""
        employees = EmployeeProfile.objects.all()
        schedules = WorkSchedule.objects.all()
        
        if not schedules.exists():
            self.stdout.write(self.style.WARNING("No work schedules found. Creating default schedule..."))
            return
        
        assigned_count = 0
        for employee in employees:
            # Skip if employee already has a schedule
            if hasattr(employee, 'work_schedule'):
                continue
            
            # Assign random schedule (you can customize this logic)
            schedule = random.choice(schedules)
            
            EmployeeSchedule.objects.create(
                employee=employee,
                schedule=schedule,
                effective_from=timezone.now().date() - timedelta(days=60)
            )
            assigned_count += 1
        
        self.stdout.write(f"Assigned schedules to {assigned_count} employees")

    def create_attendance_records(self, days):
        """Create sample attendance records"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        employees = EmployeeProfile.objects.filter(work_schedule__isnull=False)
        
        if not employees.exists():
            self.stdout.write(self.style.WARNING("No employees with schedules found."))
            return
        
        total_records = 0
        
        for employee in employees:
            schedule_info = employee.work_schedule.current_schedule
            work_days = schedule_info['work_days']
            
            current_date = start_date
            while current_date <= end_date:
                # Check if it's a working day (1=Monday, 7=Sunday)
                weekday = current_date.isoweekday()
                
                if weekday in work_days:
                    # Generate attendance with some randomness
                    attendance_prob = random.random()
                    
                    if attendance_prob > 0.05:  # 95% attendance rate
                        attendance = self.create_daily_attendance(employee, current_date)
                        if attendance:
                            total_records += 1
                
                current_date += timedelta(days=1)
        
        self.stdout.write(f"Created {total_records} attendance records")

    def create_daily_attendance(self, employee, date):
        """Create a single day's attendance record"""
        # Skip if attendance already exists
        if Attendance.objects.filter(employee=employee, date=date).exists():
            return None
        
        schedule_info = employee.work_schedule.current_schedule
        scheduled_start = schedule_info['start_time']
        scheduled_end = schedule_info['end_time']
        
        # Generate check-in time with some variation
        check_in_variation = random.randint(-20, 45)  # Minutes variation
        check_in_naive = datetime.combine(date, scheduled_start) + timedelta(minutes=check_in_variation)
        check_in_time = timezone.make_aware(check_in_naive)
        
        # Generate check-out time
        work_duration = random.uniform(7.5, 9.5)  # Hours worked
        check_out_time = check_in_time + timedelta(hours=work_duration)
        
        # Determine status based on timing
        status = 'present'
        grace_minutes = employee.work_schedule.schedule.late_grace_minutes
        
        if check_in_variation > grace_minutes:
            status = 'late'
        elif work_duration < 7:
            status = 'half_day'
        elif random.random() < 0.1:  # 10% chance of remote work
            status = 'remote'
        
        # Create attendance record
        attendance = Attendance.objects.create(
            employee=employee,
            date=date,
            check_in=timezone.make_aware(check_in_time),
            check_out=timezone.make_aware(check_out_time),
            scheduled_hours=Decimal(str(employee.work_schedule.schedule.daily_hours)),
            status=status,
            is_remote=status == 'remote',
            is_verified=True,
            check_in_ip='127.0.0.1',
            check_out_ip='127.0.0.1',
            device_info={
                'user_agent': 'Sample Data Generator',
                'platform': 'Web',
                'mobile': 'false'
            }
        )
        
        # Add some location data for non-remote work
        if status != 'remote':
            attendance.check_in_location = {
                'lat': 25.2854 + random.uniform(-0.01, 0.01),  # Doha, Qatar coordinates
                'lng': 51.5310 + random.uniform(-0.01, 0.01),
                'address': 'Office Location, Doha, Qatar'
            }
            attendance.check_out_location = attendance.check_in_location
            attendance.save()
        
        return attendance
