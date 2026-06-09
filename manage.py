#!/usr/bin/env python
import os
import sys
from pathlib import Path


def _activate_venv():
    """Activa el .venv local si no hay ningún venv activo."""
    if sys.prefix != sys.base_prefix:
        return  # ya hay un venv activo
    venv_dir = Path(__file__).resolve().parent / ".venv"
    if not venv_dir.exists():
        return
    # Insertar site-packages del venv al frente de sys.path
    import site
    py = f"python{sys.version_info.major}.{sys.version_info.minor}"
    candidates = [
        venv_dir / "Lib" / "site-packages",                  # Windows
        venv_dir / "lib" / py / "site-packages",             # Linux/macOS
    ]
    for sp in candidates:
        if sp.exists():
            site.addsitedir(str(sp))
            # Poner el ejecutable del venv en primer lugar
            venv_python = venv_dir / "Scripts" / "python.exe"
            if not venv_python.exists():
                venv_python = venv_dir / "bin" / "python"
            if venv_python.exists():
                sys.executable = str(venv_python)
            break


_activate_venv()


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "No se pudo importar Django. Asegúrate de tenerlo instalado "
            "y el entorno virtual activado."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
