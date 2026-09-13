#!/usr/bin/env python3
import ast
import csv
import sys
from pathlib import Path
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]


def fail(message):
    print(f"ERROR: {message}")
    return 1


def main():
    errors = 0
    modules = sorted(
        path for path in ROOT.glob("odental_*") if (path / "__manifest__.py").exists()
    )
    if not modules:
        errors += fail("No se encontraron módulos O Dental")

    python_count = xml_count = acl_count = 0
    for module in modules:
        required = [module / "__manifest__.py", module / "security" / "ir.model.access.csv"]
        for path in required:
            if not path.exists():
                errors += fail(f"Falta {path.relative_to(ROOT)}")

        for path in module.rglob("*.py"):
            python_count += 1
            try:
                ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            except SyntaxError as exc:
                errors += fail(f"Python inválido en {path.relative_to(ROOT)}: {exc}")

        try:
            manifest = ast.literal_eval((module / "__manifest__.py").read_text(encoding="utf-8"))
            if not manifest.get("installable"):
                errors += fail(f"{module.name} no está marcado como instalable")
            for relative_path in manifest.get("data", []):
                if not (module / relative_path).exists():
                    errors += fail(
                        f"{module.name} referencia un archivo inexistente: {relative_path}"
                    )
        except (SyntaxError, ValueError) as exc:
            errors += fail(f"No se pudo interpretar {module.name}/__manifest__.py: {exc}")

        for path in module.rglob("*.xml"):
            xml_count += 1
            try:
                ElementTree.parse(path)
            except ElementTree.ParseError as exc:
                errors += fail(f"XML inválido en {path.relative_to(ROOT)}: {exc}")

        acl_path = module / "security" / "ir.model.access.csv"
        if acl_path.exists():
            with acl_path.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            acl_count += len(rows)
            if not rows:
                errors += fail(f"La matriz de permisos de {module.name} está vacía")
            if any(not row.get("model_id:id") or not row.get("group_id:id") for row in rows):
                errors += fail(f"Hay permisos incompletos en {module.name}")

    if errors:
        return 1
    print("O Dental: validación estática aprobada")
    print(f"Módulos: {len(modules)}")
    print(f"Python: {python_count} archivos")
    print(f"XML: {xml_count} archivos")
    print(f"ACL: {acl_count} reglas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
