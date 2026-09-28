from django.contrib import admin
from .models import (
    Trust, LetterMapping, LetterMappingReadCode, LetterMappingMetric,
    LetterMappingFractureType, LetterMappingProcedureType,
    ExceptionScenarioRouting, LetterMappingAuditLog,
)


class ReadCodeInline(admin.TabularInline):
    model = LetterMappingReadCode
    extra = 0


class MetricInline(admin.TabularInline):
    model = LetterMappingMetric
    extra = 0


class FractureTypeInline(admin.TabularInline):
    model = LetterMappingFractureType
    extra = 0


class ProcedureTypeInline(admin.TabularInline):
    model = LetterMappingProcedureType
    extra = 0


class ExceptionScenarioInline(admin.TabularInline):
    model = ExceptionScenarioRouting
    extra = 0


@admin.register(LetterMapping)
class LetterMappingAdmin(admin.ModelAdmin):
    list_display = ['module_name', 'trust', 'status', 'emr_system', 'updated_at']
    list_filter = ['trust', 'status', 'emr_system']
    search_fields = ['module_name', 'letter_type']
    inlines = [ReadCodeInline, MetricInline, FractureTypeInline, ProcedureTypeInline, ExceptionScenarioInline]


admin.site.register(Trust)
admin.site.register(LetterMappingAuditLog)