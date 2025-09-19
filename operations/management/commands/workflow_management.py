from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from operations.models import WorkflowTemplate, WorkflowInstance
from operations.services.workflow_engine import WorkflowEngine

User = get_user_model()

class Command(BaseCommand):
    help = 'Manage workflows and automation'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-templates',
            action='store_true',
            help='Create sample workflow templates'
        )
        
        parser.add_argument(
            '--create-automation-rules',
            action='store_true',
            help='Create sample automation rules'
        )
        
        parser.add_argument(
            '--list-workflows',
            action='store_true',
            help='List all workflow instances'
        )
        
        parser.add_argument(
            '--start-workflow',
            type=str,
            help='Start a workflow by template name'
        )
        
        parser.add_argument(
            '--workflow-status',
            type=int,
            help='Get status of specific workflow instance'
        )
        
        parser.add_argument(
            '--active-summary',
            action='store_true',
            help='Show summary of active workflows'
        )
        
        parser.add_argument(
            '--test-engine',
            action='store_true',
            help='Test workflow engine functionality'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('=== Workflow Management System ===')
        )
        
        engine = WorkflowEngine()
        
        if options['create_templates']:
            self.create_sample_templates()
        
        if options['create_automation_rules']:
            self.create_sample_automation_rules()
        
        if options['list_workflows']:
            self.list_workflows()
        
        if options['start_workflow']:
            self.start_workflow(engine, options['start_workflow'])
        
        if options['workflow_status']:
            self.show_workflow_status(engine, options['workflow_status'])
        
        if options['active_summary']:
            self.show_active_summary(engine)
        
        if options['test_engine']:
            self.test_workflow_engine(engine)
        
        if not any(options.values()):
            self.display_help()

    def create_sample_templates(self):
        self.stdout.write("Creating sample workflow templates...")
        
        templates_data = [
            {
                'name': 'Booking Processing Workflow',
                'description': 'Automated workflow for processing new bookings',
                'category': 'booking',
                'steps': [
                    {'name': 'Validate Booking', 'type': 'automated', 'order': 1},
                    {'name': 'Assign Vendor', 'type': 'automated', 'order': 2},
                    {'name': 'Send Confirmation', 'type': 'notification', 'order': 3},
                    {'name': 'Quality Check', 'type': 'manual', 'order': 4}
                ]
            },
            {
                'name': 'Vendor Onboarding Workflow',
                'description': 'Complete vendor onboarding process',
                'category': 'vendor',
                'steps': [
                    {'name': 'Document Verification', 'type': 'manual', 'order': 1},
                    {'name': 'Background Check', 'type': 'integration', 'order': 2},
                    {'name': 'Manager Approval', 'type': 'approval', 'order': 3},
                    {'name': 'Setup Account', 'type': 'automated', 'order': 4},
                    {'name': 'Send Welcome Email', 'type': 'notification', 'order': 5}
                ]
            },
            {
                'name': 'Quality Assurance Workflow',
                'description': 'Service quality monitoring and improvement',
                'category': 'quality',
                'steps': [
                    {'name': 'Collect Feedback', 'type': 'automated', 'order': 1},
                    {'name': 'Analyze Metrics', 'type': 'automated', 'order': 2},
                    {'name': 'Quality Decision', 'type': 'decision', 'order': 3},
                    {'name': 'Generate Report', 'type': 'automated', 'order': 4}
                ]
            },
            {
                'name': 'Payment Processing Workflow',
                'description': 'Automated payment processing and reconciliation',
                'category': 'finance',
                'steps': [
                    {'name': 'Validate Payment', 'type': 'automated', 'order': 1},
                    {'name': 'Process Transaction', 'type': 'integration', 'order': 2},
                    {'name': 'Update Records', 'type': 'automated', 'order': 3},
                    {'name': 'Send Receipt', 'type': 'notification', 'order': 4}
                ]
            }
        ]
        
        created_count = 0
        
        for template_data in templates_data:
            template, created = WorkflowTemplate.objects.get_or_create(
                name=template_data['name'],
                defaults={
                    'description': template_data['description'],
                    'workflow_type': template_data['category'],
                    'trigger_type': 'event_based',
                    'is_active': True,
                    'version': 1,
                    'requires_approval': template_data['category'] in ['vendor_assignment', 'payment_processing'],
                    'priority_level': 5,
                    'estimated_duration_minutes': 60 * len(template_data['steps']),  # 60 minutes per step
                    'steps_config': template_data['steps'],
                    'conditions_config': {'default': True},
                    'automation_rules': {'auto_assign': True}
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(f"  ✓ Created template: {template_data['name']}")
                self.stdout.write(f"    Steps: {len(template_data['steps'])} configured")
            else:
                self.stdout.write(f"  → Template already exists: {template_data['name']}")
        
        self.stdout.write(f"Created {created_count} new workflow templates!")

    def create_sample_automation_rules(self):
        """Create sample automation rules"""
        from operations.models import AutomationRule, WorkflowTemplate
        
        self.stdout.write("Creating sample automation rules...")
        
        rules_data = [
            {
                'name': 'Auto-assign Vendor on Booking',
                'description': 'Automatically assign the best available vendor when a new booking is created',
                'rule_type': 'trigger',
                'trigger_event': 'booking_created',
                'conditions': {
                    'service_type': 'exists',
                    'location': 'exists'
                },
                'actions': {
                    'create_workflow': {
                        'template': 'Vendor Assignment Workflow',
                        'auto_start': True
                    }
                }
            },
            {
                'name': 'Quality Check on Service Completion',
                'description': 'Trigger quality assurance workflow when service is marked complete',
                'rule_type': 'trigger',
                'trigger_event': 'service_completed',
                'conditions': {
                    'service_value_threshold': 100
                },
                'actions': {
                    'create_workflow': {
                        'template': 'Quality Assurance Workflow',
                        'priority': 'high'
                    }
                }
            },
            {
                'name': 'Payment Processing SLA',
                'description': 'Escalate payment processing if not completed within 24 hours',
                'rule_type': 'escalation',
                'trigger_event': 'payment_received',
                'conditions': {
                    'hours_elapsed': 24,
                    'status': 'pending'
                },
                'actions': {
                    'send_notification': {
                        'recipients': ['finance@hawwa.com'],
                        'template': 'payment_escalation'
                    },
                    'create_alert': {
                        'severity': 'high',
                        'title': 'Payment Processing SLA Violation'
                    }
                }
            },
            {
                'name': 'Customer Satisfaction Follow-up',
                'description': 'Send satisfaction survey after service completion',
                'rule_type': 'action',
                'trigger_event': 'service_completed',
                'conditions': {
                    'delay_hours': 2
                },
                'actions': {
                    'send_notification': {
                        'recipients': 'customer',
                        'template': 'satisfaction_survey'
                    },
                    'create_workflow': {
                        'template': 'Customer Follow-up Workflow'
                    }
                }
            }
        ]
        
        created_count = 0
        
        for rule_data in rules_data:
            rule, created = AutomationRule.objects.get_or_create(
                name=rule_data['name'],
                defaults={
                    'description': rule_data['description'],
                    'rule_type': rule_data['rule_type'],
                    'trigger_event': rule_data['trigger_event'],
                    'conditions': rule_data['conditions'],
                    'actions': rule_data['actions'],
                    'is_active': True,
                    'priority': 5
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(f"  ✓ Created rule: {rule_data['name']}")
            else:
                self.stdout.write(f"  → Rule already exists: {rule_data['name']}")
        
        self.stdout.write(f"Created {created_count} new automation rules!")

    def _get_step_actions(self, step_type, step_name):
        """Get sample actions for different step types."""
        if step_type == 'automated':
            if 'booking' in step_name.lower():
                return {'update_booking_status': {'status': 'confirmed'}}
            elif 'vendor' in step_name.lower():
                return {'assign_vendor': {'service_type': 'general'}}
            elif 'metrics' in step_name.lower():
                return {'calculate_metrics': {'type': 'service_quality'}}
            else:
                return {'send_notification': {'type': 'info'}}
        
        elif step_type == 'notification':
            return {
                'title': f'Notification: {step_name}',
                'message': f'Automated notification for {step_name}',
                'severity': 'low'
            }
        
        elif step_type == 'integration':
            return {
                'type': 'external_api',
                'endpoint': 'https://api.example.com/verify',
                'expected_result': 'success'
            }
        
        return {}

    def _get_step_conditions(self, step_type):
        """Get sample conditions for different step types."""
        if step_type == 'approval':
            return {'user_role': 'manager'}
        elif step_type == 'decision':
            return {'booking_status': 'confirmed'}
        
        return {}

    def list_workflows(self):
        self.stdout.write("Listing workflow instances...")
        
        instances = WorkflowInstance.objects.all().order_by('-created_at')[:20]
        
        if not instances:
            self.stdout.write("  No workflow instances found")
            return
        
        self.stdout.write(f"\n  📋 Recent Workflow Instances ({instances.count()}):")
        self.stdout.write("     " + "="*80)
        
        for instance in instances:
            status_icon = {
                'pending': '⏳',
                'running': '🔄',
                'completed': '✅',
                'failed': '❌',
                'cancelled': '🚫'
            }.get(instance.status, '❓')
            
            assignee = str(instance.assigned_to) if instance.assigned_to else 'Unassigned'
            progress = f"{instance.progress_percentage or 0:.0f}%"
            
            self.stdout.write(
                f"     {status_icon} #{instance.id} - {instance.template.name}"
            )
            self.stdout.write(
                f"        Status: {instance.status.title()} | Progress: {progress} | "
                f"Assignee: {assignee}"
            )
            self.stdout.write(
                f"        Created: {instance.created_at.strftime('%Y-%m-%d %H:%M')}"
            )
            self.stdout.write("")

    def start_workflow(self, engine, template_name):
        self.stdout.write(f"Starting workflow: {template_name}")
        
        try:
            # Create workflow instance
            instance = engine.create_workflow_instance(
                template_name=template_name,
                priority='medium',
                input_data={'test_run': True, 'created_by': 'management_command'}
            )
            
            self.stdout.write(f"  ✓ Created workflow instance #{instance.id}")
            
            # Start the workflow
            success = engine.start_workflow(instance)
            
            if success:
                self.stdout.write(f"  ✓ Workflow started successfully")
                self.stdout.write(f"     Status: {instance.status}")
                self.stdout.write(f"     Progress: {instance.progress_percentage or 0:.0f}%")
                self.stdout.write(f"     Current Step: {instance.current_step or 'N/A'}")
            else:
                self.stdout.write(f"  ❌ Failed to start workflow")
                if instance.error_log:
                    self.stdout.write(f"     Error: {instance.error_log}")
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error starting workflow: {e}"))

    def show_workflow_status(self, engine, instance_id):
        self.stdout.write(f"Getting status for workflow #{instance_id}")
        
        status = engine.get_workflow_status(instance_id)
        
        if 'error' in status:
            self.stdout.write(self.style.ERROR(f"  ❌ {status['error']}"))
            return
        
        self.stdout.write(f"\n  📊 Workflow #{status['id']} Status:")
        self.stdout.write("     " + "="*50)
        self.stdout.write(f"     Template: {status['template_name']}")
        self.stdout.write(f"     Status: {status['status'].title()}")
        self.stdout.write(f"     Progress: {status['progress_percentage'] or 0:.0f}%")
        self.stdout.write(f"     Current Step: {status['current_step'] or 'N/A'}")
        
        if status['started_at']:
            self.stdout.write(f"     Started: {status['started_at'].strftime('%Y-%m-%d %H:%M')}")
        
        if status['estimated_completion']:
            self.stdout.write(f"     Est. Completion: {status['estimated_completion'].strftime('%Y-%m-%d %H:%M')}")
        
        if status['error_log']:
            self.stdout.write(f"     Error: {status['error_log']}")
        
        if status['output_data']:
            self.stdout.write(f"     Output Data: {len(status['output_data'])} entries")

    def show_active_summary(self, engine):
        self.stdout.write("Active workflows summary...")
        
        summary = engine.get_active_workflows_summary()
        
        self.stdout.write(f"\n  🎯 Active Workflows Summary:")
        self.stdout.write("     " + "="*40)
        self.stdout.write(f"     Total Active: {summary['total_active']}")
        self.stdout.write(f"     Pending: {summary['pending']}")
        self.stdout.write(f"     Running: {summary['running']}")
        
        if summary['by_template']:
            self.stdout.write(f"\n     📋 By Template:")
            for template, count in summary['by_template'].items():
                self.stdout.write(f"        {template}: {count}")
        
        if summary['by_assignee']:
            self.stdout.write(f"\n     👤 By Assignee:")
            for assignee, count in summary['by_assignee'].items():
                self.stdout.write(f"        {assignee}: {count}")

    def test_workflow_engine(self, engine):
        self.stdout.write("Testing workflow engine functionality...")
        
        # Test 1: Create a simple workflow
        self.stdout.write("\n  🧪 Test 1: Creating workflow instance")
        try:
            instance = engine.create_workflow_instance(
                template_name='Booking Processing Workflow',
                input_data={'booking_id': 1, 'test': True}
            )
            self.stdout.write(f"     ✓ Created instance #{instance.id}")
        except Exception as e:
            self.stdout.write(f"     ❌ Failed: {e}")
            return
        
        # Test 2: Start workflow
        self.stdout.write("\n  🧪 Test 2: Starting workflow")
        try:
            success = engine.start_workflow(instance)
            if success:
                self.stdout.write(f"     ✓ Workflow started")
                self.stdout.write(f"     Status: {instance.status}")
                self.stdout.write(f"     Progress: {instance.progress_percentage or 0:.0f}%")
            else:
                self.stdout.write(f"     ❌ Failed to start")
        except Exception as e:
            self.stdout.write(f"     ❌ Error: {e}")
        
        # Test 3: Get status
        self.stdout.write("\n  🧪 Test 3: Getting workflow status")
        try:
            status = engine.get_workflow_status(instance)
            if 'error' not in status:
                self.stdout.write(f"     ✓ Status retrieved")
                self.stdout.write(f"     Current status: {status['status']}")
            else:
                self.stdout.write(f"     ❌ {status['error']}")
        except Exception as e:
            self.stdout.write(f"     ❌ Error: {e}")
        
        self.stdout.write("\n  🎉 Workflow engine testing completed!")

    def display_help(self):
        self.stdout.write("\n Available commands:")
        self.stdout.write("  --create-templates        Create sample workflow templates")
        self.stdout.write("  --list-workflows          List all workflow instances")
        self.stdout.write("  --start-workflow NAME     Start a workflow by template name")
        self.stdout.write("  --workflow-status ID      Get status of specific workflow")
        self.stdout.write("  --active-summary          Show active workflows summary")
        self.stdout.write("  --test-engine             Test workflow engine functionality")
        
        self.stdout.write("\n Examples:")
        self.stdout.write("  python manage.py workflow_management --create-templates")
        self.stdout.write("  python manage.py workflow_management --start-workflow 'Booking Processing Workflow'")
        self.stdout.write("  python manage.py workflow_management --workflow-status 1")