import json

from django.core.management.base import BaseCommand, CommandError

from cases.models import Case, DataOrigin
from users.models import User


class Command(BaseCommand):
    help = "Ingest case records from JSON for a user: list of {case_number,cnr_number,case_title,state,district,status,case_type}. Idempotent."

    def add_arguments(self, p):
        p.add_argument("file"); p.add_argument("--user-email", required=True)

    def handle(self, *a, **o):
        try:
            user = User.objects.get(email=o["user_email"]); rows = json.load(open(o["file"], encoding="utf-8"))
        except (User.DoesNotExist, OSError, ValueError) as e:
            raise CommandError(str(e))
        n = 0
        for r in rows:
            key = {"user": user, "cnr_number": r["cnr_number"]} if r.get("cnr_number") else {"user": user, "case_number": r.get("case_number")}
            Case.objects.update_or_create(**key, defaults={k: v for k, v in r.items() if k in
                {"case_number", "case_title", "state", "district", "status", "case_type", "filing_year", "current_stage"}} | {"data_origin": DataOrigin.USER_PROVIDED})
            n += 1
        self.stdout.write(self.style.SUCCESS(f"Ingested {n} cases"))
