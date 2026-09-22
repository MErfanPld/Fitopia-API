"""برندینگ پنل ادمین به‌عنوان پنل مدیریت فیتوپیا / باشگاه‌ها."""
from django.contrib import admin


def configure_admin_site():
    admin.site.site_header = "پنل مدیریت فیتوپیا"
    admin.site.site_title = "Fitopia Management"
    admin.site.index_title = "مدیریت باشگاه‌ها، اعضا، مالی و عملیات"
    admin.site.site_url = "/api/swagger/"
    admin.site.enable_nav_sidebar = True
