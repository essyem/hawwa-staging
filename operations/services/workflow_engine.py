import logging
from typing import Dict, Optional, List, Any
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from operations.models import WorkflowTemplate, WorkflowInstance

User = get_user_model()
logger = logging.getLogger(__name__)

class WorkflowEngine:
    """Simplified workflow engine for automating business processes"""
    
    def __init__(self):
        self.logger = logger
    
    @transaction.atomic
    def create_workflow_instance(self, template_name: str, assignee=None,
                                input_data: Optional[Dict] = None):
        """Create a new workflow instance from a template"""
        try:
            template = WorkflowTemplate.objects.get(name=template_name, is_active=True)
            
            # Auto-assign if not specified
            auto_assign = template.automation_rules.get('auto_assign', False)
            if not assignee and auto_assign:
                assignee = self._get_best_assignee(template)
            
            instance = WorkflowInstance.objects.create(
                template=template,
                assigned_to=assignee,
                triggered_by=assignee,
                status='pending',
                context_data=input_data or {},
                progress_percentage=0
            )
            
            self.logger.info(f"Created workflow instance {instance.id} from template {template_name}")
            return instance
            
        except WorkflowTemplate.DoesNotExist:
            raise ValueError(f"Workflow template '{template_name}' not found or inactive")
        except Exception as e:
            self.logger.error(f"Error creating workflow instance: {str(e)}")
            raise
    
    @transaction.atomic
    def start_workflow(self, instance: WorkflowInstance) -> bool:
        """Start executing a workflow instance"""
        try:
            if instance.status != 'pending':
                raise ValueError(f"Workflow {instance.id} is not in pending status")
            
            # Update status and timing
            instance.status = 'running'
            instance.started_at = timezone.now()
            instance.current_step = 1
            
            # Initialize execution log
            instance.execution_log = [{
                'timestamp': timezone.now().isoformat(),
                'action': 'workflow_started',
                'message': f'Workflow started by engine',
                'step': 1
            }]
            
            # Calculate estimated completion based on template
            if instance.template.estimated_duration_minutes:
                instance.estimated_completion = timezone.now() + timezone.timedelta(
                    minutes=instance.template.estimated_duration_minutes
                )
            
            instance.save()
            
            # Execute first step
            self._execute_next_step(instance)
            
            self.logger.info(f"Started workflow instance {instance.id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting workflow {instance.id}: {str(e)}")
            instance.status = 'failed'
            instance.error_details = {'error': str(e), 'timestamp': timezone.now().isoformat()}
            instance.save()
            return False
    
    def _execute_next_step(self, instance: WorkflowInstance):
        """Execute the next step in the workflow"""
        try:
            steps_config = instance.template.steps_config
            if not steps_config or not isinstance(steps_config, list):
                self.logger.warning(f"No valid steps configuration for template {instance.template.name}")
                self._complete_workflow(instance)
                return
            
            current_step_index = instance.current_step - 1
            if current_step_index >= len(steps_config):
                self._complete_workflow(instance)
                return
            
            step_config = steps_config[current_step_index]
            step_name = step_config.get('name', f'Step {instance.current_step}')
            step_type = step_config.get('type', 'manual')
            
            self.logger.info(f"Executing step {instance.current_step}: {step_name} ({step_type})")
            
            # Add to execution log
            instance.execution_log.append({
                'timestamp': timezone.now().isoformat(),
                'action': 'step_started',
                'step': instance.current_step,
                'step_name': step_name,
                'step_type': step_type
            })
            
            # Execute step based on type
            success = self._execute_step_by_type(instance, step_config)
            
            if success:
                # Move to next step
                instance.current_step += 1
                instance.progress_percentage = (instance.current_step / len(steps_config)) * 100
                instance.execution_log.append({
                    'timestamp': timezone.now().isoformat(),
                    'action': 'step_completed',
                    'step': instance.current_step - 1,
                    'step_name': step_name
                })
                instance.save()
                
                # Continue with next step if automated
                if step_type == 'automated':
                    self._execute_next_step(instance)
            else:
                instance.status = 'failed'
                instance.error_details = {
                    'failed_step': instance.current_step,
                    'step_name': step_name,
                    'timestamp': timezone.now().isoformat()
                }
                instance.save()
                
        except Exception as e:
            self.logger.error(f"Error executing step for workflow {instance.id}: {str(e)}")
            instance.status = 'failed'
            instance.error_details = {'error': str(e), 'timestamp': timezone.now().isoformat()}
            instance.save()
    
    def _execute_step_by_type(self, instance: WorkflowInstance, step_config: Dict) -> bool:
        """Execute a step based on its type"""
        step_type = step_config.get('type', 'manual')
        
        if step_type == 'automated':
            return self._execute_automated_step(instance, step_config)
        elif step_type == 'manual':
            return self._execute_manual_step(instance, step_config)
        elif step_type == 'approval':
            return self._execute_approval_step(instance, step_config)
        elif step_type == 'notification':
            return self._execute_notification_step(instance, step_config)
        else:
            self.logger.warning(f"Unknown step type: {step_type}")
            return True  # Continue workflow
    
    def _execute_automated_step(self, instance: WorkflowInstance, step_config: Dict) -> bool:
        """Execute an automated step"""
        step_name = step_config.get('name', '')
        
        # Simple automation based on step name
        if 'booking' in step_name.lower():
            # Update booking status
            booking_id = instance.context_data.get('booking_id')
            if booking_id:
                self.logger.info(f"Auto-updating booking {booking_id}")
                instance.context_data['booking_updated'] = True
        
        elif 'vendor' in step_name.lower():
            # Auto assign vendor
            self.logger.info("Auto-assigning vendor")
            instance.context_data['vendor_assigned'] = True
        
        elif 'metrics' in step_name.lower():
            # Calculate metrics
            self.logger.info("Auto-calculating metrics")
            instance.context_data['metrics_calculated'] = True
        
        return True
    
    def _execute_manual_step(self, instance: WorkflowInstance, step_config: Dict) -> bool:
        """Execute a manual step (requires human intervention)"""
        instance.status = 'waiting_approval'
        instance.save()
        self.logger.info(f"Workflow {instance.id} waiting for manual step completion")
        return False  # Stop automated execution
    
    def _execute_approval_step(self, instance: WorkflowInstance, step_config: Dict) -> bool:
        """Execute an approval step"""
        instance.status = 'waiting_approval'
        instance.save()
        self.logger.info(f"Workflow {instance.id} waiting for approval")
        return False  # Stop automated execution
    
    def _execute_notification_step(self, instance: WorkflowInstance, step_config: Dict) -> bool:
        """Execute a notification step"""
        self.logger.info(f"Sending notification for workflow {instance.id}")
        instance.context_data['notification_sent'] = True
        return True
    
    def _complete_workflow(self, instance: WorkflowInstance):
        """Complete the workflow"""
        instance.status = 'completed'
        instance.completed_at = timezone.now()
        instance.progress_percentage = 100
        instance.execution_log.append({
            'timestamp': timezone.now().isoformat(),
            'action': 'workflow_completed',
            'message': 'Workflow completed successfully'
        })
        instance.save()
        self.logger.info(f"Completed workflow instance {instance.id}")
    
    def _get_best_assignee(self, template: WorkflowTemplate):
        """Get the best assignee for a workflow template"""
        # Simple assignment logic - could be enhanced with AI/ML
        if template.workflow_type == 'booking_processing':
            return User.objects.filter(groups__name='Operations').first()
        elif template.workflow_type == 'vendor_assignment':
            return User.objects.filter(groups__name='Vendor_Management').first()
        elif template.workflow_type == 'quality_check':
            return User.objects.filter(groups__name='Quality_Assurance').first()
        elif template.workflow_type == 'payment_processing':
            return User.objects.filter(groups__name='Finance').first()
        else:
            # Default to first superuser
            return User.objects.filter(is_superuser=True).first()
    
    def get_workflow_status(self, instance_or_id) -> Dict:
        """Get detailed status information about a workflow instance"""
        try:
            # Handle both WorkflowInstance objects and UUID strings/objects
            if isinstance(instance_or_id, WorkflowInstance):
                instance = instance_or_id
            else:
                # Try to get the instance by ID
                instance = WorkflowInstance.objects.get(id=instance_or_id)
            
            steps_config = instance.template.steps_config or []
            total_steps = len(steps_config)
            
            return {
                'id': str(instance.id),
                'template_name': instance.template.name,
                'status': instance.status,
                'current_step': instance.current_step,
                'total_steps': total_steps,
                'progress_percentage': float(instance.progress_percentage),
                'started_at': instance.started_at,
                'estimated_completion': instance.estimated_completion,
                'context_data': instance.context_data,
                'execution_log': instance.execution_log[-5:] if instance.execution_log else []  # Last 5 entries
            }
        except WorkflowInstance.DoesNotExist:
            return {'error': f'Workflow instance {instance_or_id} not found'}
        except Exception as e:
            return {'error': f'Error getting workflow status: {str(e)}'}