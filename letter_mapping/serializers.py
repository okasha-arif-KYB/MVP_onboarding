from rest_framework import serializers
from django.db import transaction
from .models import (
    Trust,
    LetterMapping,
    LetterMappingReadCode,
    LetterMappingMetric,
    LetterMappingFractureType,
    LetterMappingProcedureType,
    ExceptionScenarioRouting,
    LetterMappingAuditLog,
)


class TrustSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trust
        fields = ['id', 'name', 'default_emr_system', 'created_at']


class ReadCodeSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=False)

    class Meta:
        model = LetterMappingReadCode
        fields = ['id', 'read_code_type', 'code', 'snomed_code', 'sort_order']


class MetricSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=False)

    class Meta:
        model = LetterMappingMetric
        fields = ['id', 'metric_name', 'code_type', 'code', 'snomed_code', 'qof', 'sort_order']


class FractureTypeSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=False)

    class Meta:
        model = LetterMappingFractureType
        fields = ['id', 'code', 'snomed_code', 'description', 'sort_order']


class ProcedureTypeSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=False)

    class Meta:
        model = LetterMappingProcedureType
        fields = ['id', 'code', 'snomed_code', 'description', 'sort_order']


class ExceptionScenarioRoutingSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=False)

    class Meta:
        model = ExceptionScenarioRouting
        fields = ['id', 'scenario_name', 'note', 'forward_to', 'action_flag', 'is_custom', 'sort_order']


class AuditLogSerializer(serializers.ModelSerializer):
    changed_by_username = serializers.CharField(source='changed_by.username', read_only=True, default=None)

    class Meta:
        model = LetterMappingAuditLog
        fields = ['id', 'changed_by_username', 'field_changed', 'old_value', 'new_value', 'changed_at']


class LetterMappingSerializer(serializers.ModelSerializer):
    read_codes = ReadCodeSerializer(many=True, required=False)
    metrics = MetricSerializer(many=True, required=False)
    fracture_types = FractureTypeSerializer(many=True, required=False)
    procedure_types = ProcedureTypeSerializer(many=True, required=False)
    exception_scenarios = ExceptionScenarioRoutingSerializer(many=True, required=False)

    class Meta:
        model = LetterMapping
        fields = [
            'id', 'trust', 'module_name', 'date_basis', 'k_id', 'letter_type',
            'sender', 'dept', 'provider', 'emr_system',
            'emergency_admission_code', 'emergency_admission_snomed',
            'left_early_code', 'left_early_snomed',
            'clinical_frailty_scale',
            'confirmed_fracture_action', 'procedures_action', 'confirmed_diagnosis_action',
            'recommendations', 'status', 'created_at', 'updated_at',
            'read_codes', 'metrics', 'fracture_types', 'procedure_types', 'exception_scenarios',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    CHILD_MAP = {
        'read_codes': (LetterMappingReadCode, ReadCodeSerializer),
        'metrics': (LetterMappingMetric, MetricSerializer),
        'fracture_types': (LetterMappingFractureType, FractureTypeSerializer),
        'procedure_types': (LetterMappingProcedureType, ProcedureTypeSerializer),
        'exception_scenarios': (ExceptionScenarioRouting, ExceptionScenarioRoutingSerializer),
    }

    @transaction.atomic
    def create(self, validated_data):
        child_data = {key: validated_data.pop(key, []) for key in self.CHILD_MAP}
        letter_mapping = LetterMapping.objects.create(**validated_data)
        self._sync_children(letter_mapping, child_data)
        return letter_mapping

    @transaction.atomic
    def update(self, instance, validated_data):
        child_data = {key: validated_data.pop(key, None) for key in self.CHILD_MAP}

        for attr, value in validated_data.items():
            old_value = getattr(instance, attr)
            if str(old_value) != str(value):
                LetterMappingAuditLog.objects.create(
                    letter_mapping=instance,
                    changed_by=self.context['request'].user if self.context.get('request') else None,
                    field_changed=attr,
                    old_value=str(old_value),
                    new_value=str(value),
                )
            setattr(instance, attr, value)
        instance.save()

        for key, data in child_data.items():
            if data is not None:
                self._sync_children(instance, {key: data})

        return instance

    def _sync_children(self, letter_mapping, child_data):
        for field_name, items in child_data.items():
            model_class, _ = self.CHILD_MAP[field_name]
            related_manager = getattr(letter_mapping, field_name)

            # Replace-all strategy: simplest and safest for nested config forms
            related_manager.all().delete()
            for item in items:
                item.pop('id', None)
                model_class.objects.create(letter_mapping=letter_mapping, **item)