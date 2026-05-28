"""
Modelos read-only que mapean las tablas existentes en bdsiggo.
Todos tienen managed=False — Django nunca los toca con migraciones.
Los db_table usan la notación "schema"."tabla" de PostgreSQL.

IMPORTANTE: bdsiggo corre en PostgreSQL ~8.x (versión antigua).
Los tipos aquí reflejan el esquema real según bdsiggo.sql de referencia.
Verificar contra el servidor real antes de conectar (especialmente
usu_est/est_ado que son integer, y encoding que puede ser LATIN1).
"""
from django.db import models


class SogemUsuario(models.Model):
    usu_ide = models.AutoField(primary_key=True)
    usu_nom = models.CharField(max_length=150)
    usu_pas = models.CharField(max_length=100)
    # 1 = activo, 0 = inactivo (integer, NO char)
    usu_est = models.IntegerField(default=1)
    usu_usu = models.CharField(max_length=100, unique=True)
    per_ide = models.IntegerField(default=0)
    autenticacion = models.CharField(max_length=30, null=True, blank=True)
    auth_duracion = models.IntegerField(null=True, blank=True)
    telefono = models.CharField(max_length=15, null=True, blank=True)

    class Meta:
        managed = False
        app_label = "siggo_readonly"
        db_table = '"sogem"."usuario"'

    def __str__(self):
        return self.usu_usu


class SogemPersona(models.Model):
    per_ide = models.AutoField(primary_key=True)
    per_pat = models.CharField(max_length=200, blank=True)
    per_mat = models.CharField(max_length=200, blank=True)
    per_nom = models.CharField(max_length=200)
    fec_nac = models.DateField(null=True, blank=True)
    pai_ide = models.IntegerField(null=True, blank=True)
    per_com = models.CharField(max_length=200, null=True, blank=True)
    per_sex = models.CharField(max_length=1, null=True, blank=True)
    # DNI — clave cruzada con inventario
    per_doc = models.CharField(max_length=20, db_index=True, blank=True)
    per_ema = models.CharField(max_length=250, null=True, blank=True)
    tip_doc = models.IntegerField(default=1)
    per_dir = models.CharField(max_length=300, null=True, blank=True)
    cod_mun = models.IntegerField(null=True, blank=True)
    per_tel = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        app_label = "siggo_readonly"
        db_table = '"sogem"."persona"'

    @property
    def nombre_completo(self):
        partes = [self.per_nom.strip(), self.per_pat.strip(), self.per_mat.strip()]
        return " ".join(p for p in partes if p and p != "-")


class SiggoUnidadOrganica(models.Model):
    uni_ide = models.AutoField(primary_key=True)
    uni_abr = models.CharField(max_length=200, blank=True)
    uni_nom = models.CharField(max_length=300)
    # 0 = raíz
    uni_sup = models.IntegerField(default=0)
    uni_niv = models.IntegerField(default=0)
    # 1 = activo, 0 = inactivo (integer)
    est_ado = models.IntegerField(default=1)
    uni_loc = models.IntegerField(default=0)
    uni_alt = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        app_label = "siggo_readonly"
        db_table = '"siggo"."unidad_organica"'

    def __str__(self):
        return self.uni_nom


class SiggoSede(models.Model):
    sed_ide = models.AutoField(primary_key=True)
    sed_nom = models.TextField()
    sed_ubi = models.TextField(blank=True)
    # integer en el schema real
    est_ado = models.IntegerField(default=1)

    class Meta:
        managed = False
        app_label = "siggo_readonly"
        db_table = '"siggo"."sede"'

    def __str__(self):
        return self.sed_nom


class SiggoCargo(models.Model):
    car_ide = models.AutoField(primary_key=True)
    # trb_ide: id de trabajador en sistema de RR.HH. (puede diferir de per_ide)
    trb_ide = models.IntegerField(null=True, blank=True)
    # uni_ide: FK a siggo.unidad_organica
    uni_ide = models.IntegerField(null=True, blank=True)
    # per_ide: FK directa a sogem.persona — usar esto para cruzar con usuario
    per_ide = models.IntegerField(null=True, blank=True, db_index=True)
    car_des = models.CharField(max_length=300, blank=True)
    car_com = models.CharField(max_length=300, blank=True)
    # 1 = activo, 0 = inactivo (integer)
    est_ado = models.IntegerField(default=1)
    fch_alt = models.DateField(null=True, blank=True)
    fch_baj = models.DateField(null=True, blank=True)
    car_niv = models.IntegerField(null=True, blank=True)
    # car_pri: flag de cargo principal en siggo (>0 = principal)
    car_pri = models.IntegerField(default=0)
    car_tip = models.IntegerField(null=True, blank=True)

    class Meta:
        managed = False
        app_label = "siggo_readonly"
        db_table = '"siggo"."cargo"'

    def __str__(self):
        return self.car_des or f"Cargo {self.car_ide}"
