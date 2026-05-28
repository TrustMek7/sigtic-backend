class SiggoRouter:
    """
    Enruta todos los modelos de siggo_readonly a la BD 'siggo'.
    Bloquea migraciones y escrituras a nivel Django (no depende de
    default_transaction_read_only, que no existe en PostgreSQL 8.x).
    """

    app_label = "siggo_readonly"

    def db_for_read(self, model, **hints):
        if model._meta.app_label == self.app_label:
            return "siggo"
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == self.app_label:
            raise RuntimeError("La base de datos siggo es de solo lectura.")
        return None

    def allow_relation(self, obj1, obj2, **hints):
        labels = {obj1._meta.app_label, obj2._meta.app_label}
        if self.app_label in labels:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == self.app_label:
            return False
        return None
