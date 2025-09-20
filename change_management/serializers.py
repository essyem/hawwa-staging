from rest_framework import serializers
from .models import ChangeRequest, Incident, Lead
from .models import Comment, Activity, Role, RoleAssignment
from django.contrib.auth import get_user_model


def _user_is_operator(user):
    """Return True if the given user has the operator role."""
    if not user or not getattr(user, 'is_authenticated', False):
        return False
    return RoleAssignment.objects.filter(user=user, role__name='operator').exists()


class ChangeRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChangeRequest
        # Make assignee write-protected through standard create/update flows.
        # Assignment must be performed via the dedicated `assign` endpoint.
        fields = '__all__'
    read_only_fields = ('created_at', 'updated_at', 'assignee')
    # Make assignee readonly in default flows; assignment via `assign` action.
    def to_representation(self, instance):
        # Default representation continues to show assignee id
        return super().to_representation(instance)


class IncidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incident
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

    def validate(self, attrs):
        # If 'assignee' is present (incident uses 'reporter' and has no assignee field
        # in current model), we keep this generic in case future fields are added. For
        # now, just return attrs.
        return attrs


class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = '__all__'


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = '__all__'


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'


class RoleAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoleAssignment
        fields = '__all__'


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')
