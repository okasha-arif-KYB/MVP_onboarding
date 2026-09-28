from django.urls import path
from .views import (
    TrustListCreateView,
    TrustDetailView,
    LetterMappingListCreateView,
    LetterMappingDetailView,
    LetterMappingAuditListView,
)

urlpatterns = [
    path('trusts/', TrustListCreateView.as_view(), name='trust-list-create'),
    path('trusts/<uuid:pk>/', TrustDetailView.as_view(), name='trust-detail'),

    path('letter_mappings/', LetterMappingListCreateView.as_view(), name='letter-mapping-list-create'),
    path('letter_mappings/<uuid:pk>/', LetterMappingDetailView.as_view(), name='letter-mapping-detail'),
    path('letter_mappings/<uuid:letter_mapping_id>/audit_log/', LetterMappingAuditListView.as_view(), name='letter-mapping-audit-log'),
]