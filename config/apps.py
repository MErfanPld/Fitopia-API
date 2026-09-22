from django.apps import AppConfig


class ConfigConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "config"
    verbose_name = "پیکربندی"

    def ready(self):
        from config.admin_branding import configure_admin_site

        configure_admin_site()
