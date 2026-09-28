from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from letter_mapping.models import (
    Trust,
    LetterMapping,
    LetterMappingReadCode,
    LetterMappingMetric,
    LetterMappingFractureType,
    LetterMappingProcedureType,
    ExceptionScenarioRouting,
)

User = get_user_model()


class Command(BaseCommand):
    help = "Seed the database with a demo Trust, User, and LetterMapping (with all nested children)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete existing Trust/LetterMapping rows before seeding.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["flush"]:
            self.stdout.write("Flushing existing LetterMapping and Trust rows...")
            LetterMapping.objects.all().delete()
            Trust.objects.all().delete()

        # 1. User (used for created_by / updated_by / changed_by)
        user, created = User.objects.get_or_create(
            username="okasha",
            defaults={"email": "okasha@example.com", "is_staff": True, "is_superuser": True},
        )
        if created:
            user.set_password("password123")
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Created user '{user.username}' (password: password123)"))
        else:
            self.stdout.write(f"Using existing user '{user.username}'")

        # 2. Trust
        trust, _ = Trust.objects.get_or_create(
            name="North East London NHS Trust",
            defaults={"default_emr_system": "EMIS"},
        )
        self.stdout.write(self.style.SUCCESS(f"Trust ready: {trust.name} ({trust.id})"))

        # 3. LetterMapping
        mapping, created = LetterMapping.objects.get_or_create(
            trust=trust,
            module_name="Fracture Clinic Letters",
            defaults=dict(
                date_basis=LetterMapping.DateBasis.INCIDENT_DATE,
                k_id="K-10293",
                letter_type="Outpatient Follow-up",
                sender="Dr. A. Khan",
                dept="Orthopaedics",
                provider="Central Hospital",
                emr_system=LetterMapping.EmrSystem.EMIS,
                emergency_admission_code="EM001",
                emergency_admission_snomed="1067731000000105",
                left_early_code="LE002",
                left_early_snomed="1067741000000101",
                clinical_frailty_scale=[1, 2, 3, 4, 5, 6, 7],
                confirmed_fracture_action=LetterMapping.CodeAction.CODE,
                procedures_action=LetterMapping.CodeAction.CODE,
                confirmed_diagnosis_action=LetterMapping.CodeAction.CODE,
                recommendations="Review in 6 weeks, repeat imaging if pain persists.",
                status=LetterMapping.Status.DRAFT,
                created_by=user,
                updated_by=user,
            ),
        )

        if not created:
            self.stdout.write("LetterMapping already exists — clearing its children before reseeding them.")
            mapping.read_codes.all().delete()
            mapping.metrics.all().delete()
            mapping.fracture_types.all().delete()
            mapping.procedure_types.all().delete()
            mapping.exception_scenarios.all().delete()

        # 4. Nested children
        LetterMappingReadCode.objects.create(
            letter_mapping=mapping,
            read_code_type="Diagnosis",
            code="S52.5",
            snomed_code="263204007",
            sort_order=1,
        )
        LetterMappingReadCode.objects.create(
            letter_mapping=mapping,
            read_code_type="Procedure",
            code="W20.1",
            snomed_code="429554009",
            sort_order=2,
        )

        LetterMappingMetric.objects.create(
            letter_mapping=mapping,
            metric_name="Fracture Risk Assessment",
            code_type="CODE",
            code="38341003",
            snomed_code="38341003",
            qof=True,
            sort_order=1,
        )

        LetterMappingFractureType.objects.create(
            letter_mapping=mapping,
            code="FX01",
            snomed_code="125605004",
            description="Closed fracture of wrist",
            sort_order=1,
        )

        LetterMappingProcedureType.objects.create(
            letter_mapping=mapping,
            code="PR01",
            snomed_code="182813001",
            description="Closed reduction of fracture",
            sort_order=1,
        )

        ExceptionScenarioRouting.objects.create(
            letter_mapping=mapping,
            scenario_name="Patient declined treatment",
            note="Documented refusal, no further action coded.",
            forward_to="GP",
            action_flag="REVIEW",
            is_custom=False,
            sort_order=1,
        )

        self.stdout.write(self.style.SUCCESS(
            f"Seeded LetterMapping '{mapping.module_name}' ({mapping.id}) with all nested child records."
        ))
        self.stdout.write(self.style.SUCCESS("Done."))