import uuid
from django.conf import settings
from django.db import models


class Trust(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    default_emr_system = models.CharField(
        max_length=20,
        choices=[('EMIS', 'EMIS'), ('SystmOne', 'SystmOne')],
        default='EMIS',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class LetterMapping(models.Model):
    class DateBasis(models.TextChoices):
        INCIDENT_DATE = 'Incident Date', 'Incident Date'
        CURRENT_DATE = 'Current Date', 'Current Date'

    class CodeAction(models.TextChoices):
        CODE = 'CODE', 'CODE'
        DO_NOT_CODE = 'DO NOT CODE', 'DO NOT CODE'

    class EmrSystem(models.TextChoices):
        EMIS = 'EMIS', 'EMIS'
        SYSTMONE = 'SystmOne', 'SystmOne'

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        SAVED = 'saved', 'Saved'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trust = models.ForeignKey(Trust, on_delete=models.CASCADE, related_name='letter_mappings')

    module_name = models.CharField(max_length=100)
    date_basis = models.CharField(max_length=20, choices=DateBasis.choices, default=DateBasis.INCIDENT_DATE)
    k_id = models.CharField(max_length=255, blank=True, null=True)
    letter_type = models.CharField(max_length=100, blank=True)
    sender = models.CharField(max_length=255, blank=True)
    dept = models.CharField(max_length=255, blank=True)
    provider = models.CharField(max_length=255, blank=True)
    emr_system = models.CharField(max_length=20, choices=EmrSystem.choices, default=EmrSystem.EMIS)

    emergency_admission_code = models.CharField(max_length=50, blank=True, null=True)
    emergency_admission_snomed = models.CharField(max_length=50, blank=True, null=True)

    left_early_code = models.CharField(max_length=50, blank=True, null=True)
    left_early_snomed = models.CharField(max_length=50, blank=True, null=True)

    clinical_frailty_scale = models.JSONField(default=list, blank=True)

    confirmed_fracture_action = models.CharField(max_length=20, choices=CodeAction.choices, default=CodeAction.DO_NOT_CODE)
    procedures_action = models.CharField(max_length=20, choices=CodeAction.choices, default=CodeAction.CODE)
    confirmed_diagnosis_action = models.CharField(max_length=20, choices=CodeAction.choices, default=CodeAction.CODE)

    recommendations = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['trust', 'module_name'], name='unique_module_per_trust'),
        ]

    def __str__(self):
        return f'{self.module_name} ({self.trust.name})'


class LetterMappingReadCode(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    letter_mapping = models.ForeignKey(LetterMapping, on_delete=models.CASCADE, related_name='read_codes')
    read_code_type = models.CharField(max_length=100)
    code = models.CharField(max_length=50)
    snomed_code = models.CharField(max_length=50, blank=True, null=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return f'{self.read_code_type} - {self.code}'


class LetterMappingMetric(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    letter_mapping = models.ForeignKey(LetterMapping, on_delete=models.CASCADE, related_name='metrics')
    metric_name = models.CharField(max_length=100)
    code_type = models.CharField(max_length=20, default='CODE')
    code = models.CharField(max_length=50)
    snomed_code = models.CharField(max_length=50, blank=True, null=True)
    qof = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return self.metric_name


class LetterMappingFractureType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    letter_mapping = models.ForeignKey(LetterMapping, on_delete=models.CASCADE, related_name='fracture_types')
    code = models.CharField(max_length=50)
    snomed_code = models.CharField(max_length=50, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order']


class LetterMappingProcedureType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    letter_mapping = models.ForeignKey(LetterMapping, on_delete=models.CASCADE, related_name='procedure_types')
    code = models.CharField(max_length=50)
    snomed_code = models.CharField(max_length=50, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order']


class ExceptionScenarioRouting(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    letter_mapping = models.ForeignKey(LetterMapping, on_delete=models.CASCADE, related_name='exception_scenarios')
    scenario_name = models.CharField(max_length=150)
    note = models.TextField(blank=True)
    forward_to = models.CharField(max_length=255, blank=True)
    action_flag = models.CharField(max_length=50, blank=True)
    is_custom = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return self.scenario_name


class LetterMappingAuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    letter_mapping = models.ForeignKey(LetterMapping, on_delete=models.CASCADE, related_name='audit_logs')
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    field_changed = models.CharField(max_length=100)
    old_value = models.TextField(blank=True, null=True)
    new_value = models.TextField(blank=True, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-changed_at']