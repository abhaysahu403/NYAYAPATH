from django.core.management.base import BaseCommand
from django.utils import timezone

from cases.models import Case, CaseEvent, CaseParty, DataOrigin
from courts.models import Court
from judgments.models import Judgment
from legal_research.demo_data import COURTS, JUDGMENTS, LEGAL_INFO
from legal_research.services.indexing import index_judgment, index_text
from sources.models import Source, SourceType, VerificationStatus
from users.models import User, UserRole


class Command(BaseCommand):
    help = "Seed DEMO courts, sources, judgments, a demo user and a demo case. Idempotent. Never marks anything VERIFIED."

    def add_arguments(self, p):
        p.add_argument("--password", default="DemoPass#12345")
        p.add_argument("--skip-user", action="store_true")

    def handle(self, *a, **o):
        courts = {}
        for c in COURTS:
            courts[c["name"]], _ = Court.objects.get_or_create(name=c["name"], defaults={k: v for k, v in c.items() if k != "name"})
        for r in LEGAL_INFO:
            s, _ = Source.objects.update_or_create(
                source_type=SourceType.LEGAL_INFORMATION, identifier=r["identifier"],
                defaults=dict(title=r["title"], url=r["url"], is_demo_data=True, verification_status=VerificationStatus.UNVERIFIED,
                              metadata={"key": r["key"], "demo": True}, verification_notes="DEMO summary; confirm on the official site."))
            index_text(s, r["text"], topics=r["topics"], state=r["state"])
        for r in JUDGMENTS:
            s, _ = Source.objects.update_or_create(
                source_type=SourceType.JUDGMENT, identifier=r["identifier"],
                defaults=dict(title=r["title"], court=r["court"], is_demo_data=True, verification_status=VerificationStatus.UNVERIFIED,
                              metadata={"key": r["key"], "demo": True},
                              verification_notes="DEMO record. Check any citation against official sources before use."))
            j, _ = Judgment.objects.update_or_create(
                source=s, defaults=dict(title=r["title"], court=courts[r["court"]], citation=r["citation"], state=r["state"],
                                        district=r.get("district"), legal_topics=r["topics"], summary=r["summary"], full_text=r["text"],
                                        is_demo_data=True, verification_status="DEMO"))
            index_judgment(j)
        if not o["skip_user"]:
            u, created = User.objects.get_or_create(email="demo@nyayapath.local",
                                                    defaults=dict(name="Demo Citizen", preferred_language="hi", role=UserRole.CITIZEN))
            if created:
                u.set_password(o["password"]); u.save()
            case, made = Case.objects.get_or_create(user=u, case_number="DEMO RCS 123/2021", defaults=dict(
                case_type="CIVIL", case_title="[DEMO] Land possession suit", court=courts["District and Sessions Court, Bhopal"],
                state="Madhya Pradesh", district="Bhopal", filing_year=2021, status="PENDING", is_demo_data=True,
                data_origin=DataOrigin.DEMO, description="DEMO case record for development."))
            if made:
                CaseParty.objects.create(case=case, party_type="PETITIONER", name="[DEMO] Petitioner")
                CaseEvent.objects.create(case=case, event_type="CASE_FILED", event_date=timezone.now().date().replace(year=2021, month=3, day=1),
                                         title="Case filed (DEMO)", data_origin=DataOrigin.DEMO)
            self.stdout.write(f"Demo user: demo@nyayapath.local / {o['password']}")
        self.stdout.write(self.style.SUCCESS("Demo data seeded (all DEMO, none VERIFIED)."))
