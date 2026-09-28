from rest_framework import generics, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Trust, LetterMapping
from .serializers import TrustSerializer, LetterMappingSerializer, AuditLogSerializer


class TrustListCreateView(generics.ListCreateAPIView):
    queryset = Trust.objects.all()
    serializer_class = TrustSerializer


class TrustDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Trust.objects.all()
    serializer_class = TrustSerializer


class LetterMappingListCreateView(generics.ListCreateAPIView):
    queryset = LetterMapping.objects.all().select_related('trust').prefetch_related(
        'read_codes', 'metrics', 'fracture_types', 'procedure_types', 'exception_scenarios'
    )
    serializer_class = LetterMappingSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['trust', 'status', 'module_name']
    search_fields = ['module_name', 'letter_type']

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(created_by=user, updated_by=user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_queryset(self):
        return super().get_queryset().order_by('module_name')


class LetterMappingDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = LetterMapping.objects.all().select_related('trust').prefetch_related(
        'read_codes', 'metrics', 'fracture_types', 'procedure_types', 'exception_scenarios'
    )
    serializer_class = LetterMappingSerializer

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class LetterMappingAuditListView(generics.ListAPIView):
    """Read-only audit trail for a given letter mapping."""
    serializer_class = AuditLogSerializer

    def get_queryset(self):
        letter_mapping_id = self.kwargs.get('letter_mapping_id')
        return LetterMapping.objects.get(id=letter_mapping_id).audit_logs.all()