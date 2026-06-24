import os
import uuid
import time
from django.utils.text import slugify


def upload_user_avatar(instance, filename):
    short_name = slugify(instance.phone_number or "user", allow_unicode=True)[:50]
    ext = filename.split('.')[-1]
    unique_name = f"{int(time.time())}_{uuid.uuid4().hex[:8]}_{short_name}.{ext}"
    return os.path.join('uploads/user/avatar', unique_name)