"""Genera el Excel, las tablas y las figuras del caso predeterminado."""
from pathlib import Path
import csv
import json
from exportar import crear_excel, preparar_tabla
from graficas import (comparar_metodos, comparar_escenarios, comparar_temperaturas,
                       comparar_errores, guardar_grafica)
from modelo import escenarios_predeterminados, simular


def generar():
    carpeta = Path(__file__).parent / "resultados"
    figuras = carpeta / "figuras"
    figuras.mkdir(parents=True, exist_ok=True)
    resultados = [simular(p) for p in escenarios_predeterminados()]
    (carpeta / "CORE_DeltaT_Fase2_Resultados.xlsx").write_bytes(crear_excel(resultados))
    tabla = preparar_tabla(resultados)
    with (carpeta / "CORE_DeltaT_Fase2_Resultados.csv").open("w", newline="", encoding="utf-8-sig") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=list(tabla[0]))
        escritor.writeheader()
        escritor.writerows(tabla)
    (carpeta / "datos_simulacion.json").write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")
    graficas = {"metodos_procesador_base": comparar_metodos(resultados[0], 0),
                "metodos_disipador_base": comparar_metodos(resultados[0], 1),
                "escenarios_procesador": comparar_escenarios(resultados, 0),
                "escenarios_disipador": comparar_escenarios(resultados, 1),
                "dos_temperaturas_base": comparar_temperaturas(resultados[0]),
                "errores_base": comparar_errores(resultados[0])}
    for nombre, figura in graficas.items():
        (figuras / (nombre + ".png")).write_bytes(guardar_grafica(figura))
    return resultados


if __name__ == "__main__":
    generar()
