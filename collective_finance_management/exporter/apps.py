from django.apps import AppConfig


class ExporterConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "exporter"

    def ready(self):
        # exporter owns its sources and is allowed to depend on ledger's
        # models directly - ledger has no knowledge of exporter.
        from .registry import register_source
        from .sources.euer import EuerVereinSource
        from .sources.afa_anlagen import AfaAnlagenSource

        register_source(EuerVereinSource())
        register_source(AfaAnlagenSource())
