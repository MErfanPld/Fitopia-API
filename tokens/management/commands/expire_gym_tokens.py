"""
علامت‌گذاری توکن‌های منقضی‌شده (بعد از نیمه‌شب) در دیتابیس.

Redis خودش با TTL پاک می‌شود؛ این دستور وضعیت DB را هم‌تراز می‌کند.

پیشنهاد cron (هر روز ۰۰:۰۵ به وقت Asia/Tehran):
0 5 0 * * * cd /path/to/project && python manage.py expire_gym_tokens
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from tokens.models import GymToken
from tokens.redis_store import delete_token


class Command(BaseCommand):
    help = "Expire active gym tokens past valid_until (midnight reset)."

    def handle(self, *args, **options):
        now = timezone.now()
        qs = GymToken.objects.filter(status="active", valid_until__lte=now)
        count = 0
        for token in qs.iterator():
            token.status = "expired"
            token.save(update_fields=["status"])
            delete_token(token.token_code)
            count += 1
        self.stdout.write(self.style.SUCCESS(f"Expired {count} token(s)."))
