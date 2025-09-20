from rest_framework import serializers
from .models import ChangeRequest, Incident, Lead


class ChangeRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChangeRequest
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class IncidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incident
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')
