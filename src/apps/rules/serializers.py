from rest_framework import serializers

from .models import Rule


class RuleSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = Rule
        fields = ['id', 'name', 'condition', 'is_active', 'created_by', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class RuleEvaluationRequestSerializer(serializers.Serializer):
    rules = serializers.ListField(
        child=serializers.CharField(),
        min_length=1
    )
    payload = serializers.JSONField()


class RuleEvaluationResponseSerializer(serializers.Serializer):
    result = serializers.CharField()
    passed_rules = serializers.ListField(child=serializers.CharField())
    failed_rules = serializers.ListField(child=serializers.CharField())


class RuleEvaluationAsyncResponseSerializer(serializers.Serializer):
    task_id = serializers.CharField()
    status = serializers.CharField()
    message = serializers.CharField()
