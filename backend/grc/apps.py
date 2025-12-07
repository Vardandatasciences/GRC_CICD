from django.apps import AppConfig


class GrcConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "grc"
    
    def ready(self):
        # Import signal handlers when the app is ready
        import grc.signals.event_signals