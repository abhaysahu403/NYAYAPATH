import json
from datetime import date

from django.core.management.base import BaseCommand, CommandError

from courts.models import Court
from judgments.models import Judgment
from legal_research.services.indexing import index_judgment
from sources.models import Source, SourceType, VerificationStatus


class Command(BaseCommand):
    help = ("Ingest judgments from a JSON file: list of {identifier,title,citation,court,court_type,state,district,date(YYYY-MM-DD),"
            "topics[],summary,full_text,source_url}. Idempotent on identifier. Records are UNVERIFIED unless --mark-verified.")

    def add_arguments(self, p):
        p.add_argument("file")
        p.add_argument("--mark-verified", action="store_true", help="Only use after checking against official sources")

    def handle(self, *a, **o):
        try:
            rows = json.load(open(o["file"], encoding="utf-8"))
        except (OSError, ValueError) as e:
            raise CommandError(f"Cannot read file: {e}")
        n = 0
        for r in rows:
            if not r.get("identifier") or not r.get("title"):
                self.stderr.write("skipped record without identifier/title"); continue
            court = None
            if r.get("court"):
                court, _ = Court.objects.get_or_create(name=r["court"], defaults={"court_type": r.get("court_type", "OTHER"), "state": r.get("state")})
            ver = VerificationStatus.VERIFIED if o["mark_verified"] else VerificationStatus.UNVERIFIED
            s, _ = Source.objects.update_or_create(source_type=SourceType.JUDGMENT, identifier=r["identifier"],
                                                   defaults=dict(title=r["title"], url=r.get("source_url"), court=r.get("court"), verification_status=ver))
            d = date.fromisoformat(r["date"]) if r.get("date") else None
            j, _ = Judgment.objects.update_or_create(source=s, defaults=dict(
                title=r["title"], court=court, citation=r.get("citation"), judgment_date=d, state=r.get("state"), district=r.get("district"),
                legal_topics=r.get("topics", []), summary=r.get("summary"), full_text=r.get("full_text"), source_url=r.get("source_url"),
                verification_status="VERIFIED" if o["mark_verified"] else "UNVERIFIED"))
            index_judgment(j); n += 1
        self.stdout.write(self.style.SUCCESS(f"Ingested {n} judgments"))
