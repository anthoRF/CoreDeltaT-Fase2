"""Exportación de las mismas series que se muestran en la aplicación."""
from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter


def preparar_tabla(resultados):
    columnas = ["Escenario", "Tiempo (s)", "Tc analítica (°C)", "Tc Euler (°C)",
                "Tc Euler mejorado (°C)", "Td analítica (°C)", "Td Euler (°C)",
                "Td Euler mejorado (°C)"]
    filas = []
    for r in resultados:
        for indice, tiempo in enumerate(r["tiempos"]):
            filas.append([r["parametros"]["nombre"], tiempo,
                          r["exactas"][indice][0], r["series"]["Euler"][indice][0],
                          r["series"]["Heun"][indice][0], r["exactas"][indice][1],
                          r["series"]["Euler"][indice][1], r["series"]["Heun"][indice][1]])
    return [dict(zip(columnas, fila)) for fila in filas]


def preparar_hojas(resultados):
    tabla = preparar_tabla(resultados)
    filas_resultados = [list(tabla[0])] + [list(fila.values()) for fila in tabla]
    parametros = [["Parámetro", *[r["parametros"]["nombre"] for r in resultados], "Unidad"]]
    entradas = [("Potencia térmica P", "potencia", "W"),
                ("Temperatura ambiente Ta", "ambiente", "°C"),
                ("Temperatura inicial Tc", "inicial_c", "°C"),
                ("Temperatura inicial Td", "inicial_d", "°C"),
                ("Capacidad del procesador Cc", "capacidad_c", "J/°C"),
                ("Capacidad del disipador Cd", "capacidad_d", "J/°C"),
                ("Conductancia entre cuerpos g", "acoplamiento", "W/°C"),
                ("Conductancia ambiental h", "conductancia", "W/°C"),
                ("Duración", "duracion", "s")]
    for nombre, clave, unidad in entradas:
        parametros.append([nombre, *[r["parametros"][clave] for r in resultados], unidad])
    parametros.append(["Paso efectivo", *[r["paso"] for r in resultados], "s"])
    parametros.append(["Instantes", *[len(r["tiempos"]) for r in resultados], "—"])
    for nombre, clave in (("Equilibrio del procesador", "equilibrio_c"),
                          ("Equilibrio del disipador", "equilibrio_d")):
        parametros.append([nombre, *[r["datos"][clave] for r in resultados], "°C"])
    for componente, nombre in ((0, "Tc final"), (1, "Td final")):
        parametros.append([nombre, *[r["exactas"][-1][componente] for r in resultados], "°C"])
    for metodo, nombre in (("Euler", "Euler"), ("Heun", "Euler mejorado")):
        for clave, componente in (("error_c", "Tc"), ("error_d", "Td")):
            parametros.append([f"Error máximo {componente} · {nombre}",
                               *[r["resumen"][metodo][clave] for r in resultados], "°C"])
    return {"Resultados": filas_resultados, "Parámetros": parametros}


def crear_excel(resultados):
    libro = Workbook()
    libro.remove(libro.active)
    for nombre, filas in preparar_hojas(resultados).items():
        hoja = libro.create_sheet(nombre)
        for fila in filas:
            hoja.append(fila)
        hoja.sheet_view.showGridLines = False
        for fila in hoja:
            for celda in fila:
                celda.font = Font(name="Arial", size=10, color="172B3A")
                celda.alignment = Alignment(vertical="center")
                if isinstance(celda.value, (int, float)):
                    celda.number_format = "0.0000"
            hoja.row_dimensions[fila[0].row].height = 20
        for celda in hoja[1]:
            celda.font = Font(name="Arial", size=10, bold=True, color="172B3A")
            celda.fill = PatternFill("solid", fgColor="EEF1F3")
            celda.border = Border(bottom=Side(style="thin", color="7A8790"))
            celda.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        hoja.row_dimensions[1].height = 36
        anchos = [23, 14, 23, 22, 26, 23, 22, 26] if nombre == "Resultados" else [44, 23, 23, 23, 16]
        for indice, ancho in enumerate(anchos, start=1):
            hoja.column_dimensions[get_column_letter(indice)].width = ancho
        if nombre == "Resultados":
            hoja.freeze_panes = "C2"
        else:
            for celda in hoja[12][1:4]:
                celda.number_format = "0"
            for fila in hoja.iter_rows(min_row=2, min_col=5, max_col=5):
                fila[0].alignment = Alignment(horizontal="center", vertical="center")
        hoja.page_setup.orientation = "landscape"
        hoja.page_setup.paperSize = hoja.PAPERSIZE_A4
        hoja.page_setup.fitToWidth = 1
        hoja.page_setup.fitToHeight = 0
        hoja.sheet_properties.pageSetUpPr.fitToPage = True
        hoja.print_title_rows = "1:1"
        hoja.print_area = hoja.dimensions
    libro.properties.title = "CORE ΔT — Procesador y disipador"
    libro.properties.creator = "CORE ΔT"
    archivo = BytesIO()
    libro.save(archivo)
    return archivo.getvalue()
