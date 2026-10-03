from urllib.parse import urlparse

from django.core.management.base import BaseCommand
from django.utils import timezone

from sources.models import Source, VerificationStatus


class Command(BaseCommand):
    help = ("Structural source check (title, https URL, identifier). Demo sources are NEVER promoted. "
            "Real sources are only marked VERIFIED with --promote after a human has checked them against official sites.")

    def add_arguments(self, p):
        p.add_argument("--promote", action="store_true")

    def handle(self, *a, **o):
        bad = ok = 0
        for s in Source.objects.exclude(source_type="USER_DOCUMENT"):
            problems = []
            if not s.title: problems.append("no title")
            if s.url and urlparse(s.url).scheme != "https": problems.append("non-https url")
            if not s.identifier: problems.append("no identifier")
            if problems:
                bad += 1; self.stdout.write(f"PROBLEM {s.id}: {', '.join(problems)}")
                if not s.is_demo_data and s.verification_status == VerificationStatus.VERIFIED:
                    s.verification_status = VerificationStatus.FAILED; s.verification_notes = "; ".join(problems); s.save()
            else:
                ok += 1
                if o["promote"] and not s.is_demo_data and s.verification_status != VerificationStatus.VERIFIED:
                    s.verification_status = VerificationStatus.VERIFIED; s.verified_at = timezone.now(); s.save()
        self.stdout.write(self.style.SUCCESS(f"{ok} ok, {bad} with problems"))
