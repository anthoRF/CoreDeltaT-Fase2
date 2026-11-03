"""Gráficas científicas de temperaturas y errores."""
from io import BytesIO
from matplotlib.figure import Figure
from modelo import METODOS, NOMBRES

AZUL = "#17304F"
VERDE = "#205847"
ROJO = "#8A3B3F"
COLORES = {"Euler": ROJO, "Heun": VERDE}


def crear_grafica(etiqueta_y="Temperatura (°C)"):
    figura = Figure(figsize=(6.5, 3.9), layout="constrained")
    eje = figura.subplots()
    eje.set_xlabel("Tiempo (s)", fontsize=10, color=AZUL)
    eje.set_ylabel(etiqueta_y, fontsize=10, color=AZUL)
    eje.tick_params(labelsize=9, colors=AZUL)
    eje.spines[["top", "right"]].set_visible(False)
    for lado in ("bottom", "left"):
        eje.spines[lado].set_color("#AFB9BD")
    eje.grid(axis="y", color="#E7ECE9", linewidth=0.7)
    eje.set_axisbelow(True)
    eje.margins(x=0)
    eje.ticklabel_format(axis="y", style="plain", useOffset=False)
    return figura, eje


def guardar_grafica(figura):
    archivo = BytesIO()
    figura.savefig(archivo, format="png", dpi=300, facecolor="white")
    return archivo.getvalue()


def comparar_metodos(r, componente=0):
    figura, eje = crear_grafica()
    eje.plot(r["tiempos"], [v[componente] for v in r["exactas"]],
             color=AZUL, linewidth=2.2, label="Analítica")
    for metodo, estilo, marca in (("Euler", ":", "o"), ("Heun", "--", "s")):
        eje.plot(r["tiempos"], [v[componente] for v in r["series"][metodo]],
                 color=COLORES[metodo], linestyle=estilo, linewidth=1.25,
                 marker=marca, markersize=3, markevery=max(1, (len(r["tiempos"]) - 1) // 12),
                 label=NOMBRES[metodo])
    eje.legend(frameon=False, fontsize=9, ncol=3)
    return figura


def comparar_escenarios(resultados, componente=0):
    figura, eje = crear_grafica()
    for r, color, estilo in zip(resultados, (AZUL, ROJO, VERDE), ("-", "--", "-.")):
        eje.plot(r["tiempos"], [v[componente] for v in r["exactas"]],
                 color=color, linestyle=estilo, linewidth=1.9, label=r["parametros"]["nombre"])
    eje.legend(frameon=False, fontsize=9)
    return figura


def comparar_temperaturas(r):
    figura, eje = crear_grafica()
    for componente, nombre, color in ((0, "Procesador", AZUL), (1, "Disipador", VERDE)):
        eje.plot(r["tiempos"], [v[componente] for v in r["exactas"]],
                 color=color, linewidth=1.9, label=nombre)
        equilibrio = r["datos"]["equilibrio_c" if componente == 0 else "equilibrio_d"]
        eje.axhline(equilibrio, color=color, linestyle=":", linewidth=0.9)
    eje.legend(frameon=False, fontsize=9)
    return figura


def comparar_errores(r):
    figura, eje = crear_grafica("Error absoluto máximo de Tc y Td (°C)")
    for metodo in METODOS:
        eje.plot(r["tiempos"], [max(error) for error in r["errores"][metodo]],
                 color=COLORES[metodo], linewidth=1.7, label=NOMBRES[metodo])
    eje.legend(frameon=False, fontsize=9)
    return figura
