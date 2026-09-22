from django.apps import AppConfig


class GymPanelConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "gym_panel"
    verbose_name = "مدیریت باشگاه‌ها"

    def ready(self):
        from config.admin_branding import configure_admin_site

        configure_admin_site()
