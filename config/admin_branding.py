"""برندینگ فارسی پنل ادمین فیتوپیا."""
from django.contrib import admin


def configure_admin_site():
    admin.site.site_header = "پنل مدیریت فیتوپیا"
    admin.site.site_title = "مدیریت فیتوپیا"
    admin.site.index_title = "داشبورد مدیریت باشگاه‌ها"
    admin.site.site_url = "/api/swagger/"
    admin.site.enable_nav_sidebar = True
