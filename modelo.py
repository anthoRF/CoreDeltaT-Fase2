"""Balance térmico, solución analítica, Euler y Euler mejorado."""
from math import ceil, exp, expm1, isclose, isfinite, sqrt

METODOS = ("Euler", "Heun")
NOMBRES = {"Euler": "Euler", "Heun": "Euler mejorado"}


def escenarios_predeterminados():
    comunes = dict(ambiente=25.0, inicial_c=25.0, inicial_d=25.0,
                   capacidad_c=10.0, capacidad_d=10.0, acoplamiento=1.0,
                   duracion=180.0, paso_solicitado=1.0)
    return construir_escenarios(comunes, 18.0, 24.0, 0.5, 0.75)


def construir_escenarios(comunes, potencia_base, potencia_alternativa,
                         conductancia_base, conductancia_alternativa):
    """Cada alternativa modifica una sola entrada del caso base."""
    if potencia_base == potencia_alternativa:
        raise ValueError("Las potencias base y alternativa deben ser distintas.")
    if conductancia_base == conductancia_alternativa:
        raise ValueError("Las conductancias base y alternativa deben ser distintas.")
    nombre_p = "Mayor potencia" if potencia_alternativa > potencia_base else "Menor potencia"
    nombre_h = "Mayor disipación" if conductancia_alternativa > conductancia_base else "Menor disipación"
    return [dict(comunes, nombre="Base", potencia=potencia_base, conductancia=conductancia_base),
            dict(comunes, nombre=nombre_p, potencia=potencia_alternativa, conductancia=conductancia_base),
            dict(comunes, nombre=nombre_h, potencia=potencia_base, conductancia=conductancia_alternativa)]


def validar(p):
    claves = ("potencia", "ambiente", "inicial_c", "inicial_d", "capacidad_c",
              "capacidad_d", "acoplamiento", "conductancia", "duracion", "paso_solicitado")
    for clave in claves:
        valor = p.get(clave)
        if isinstance(valor, bool) or not isinstance(valor, (int, float)) or not isfinite(valor):
            raise ValueError("Todos los parámetros deben ser números finitos.")
    if p["potencia"] < 0:
        raise ValueError("La potencia debe ser mayor o igual a cero.")
    for clave in ("capacidad_c", "capacidad_d", "acoplamiento", "conductancia", "duracion", "paso_solicitado"):
        if p[clave] <= 0:
            raise ValueError("Las capacidades, las conductancias, la duración y el paso deben ser positivos.")
    if min(p["ambiente"], p["inicial_c"], p["inicial_d"]) < -273.15:
        raise ValueError("Las temperaturas no pueden ser inferiores a −273,15 °C.")


def caracterizar(p):
    """Obtiene los coeficientes de x'' + alfa*x' + beta*x = q."""
    validar(p)
    cc, cd = p["capacidad_c"], p["capacidad_d"]
    g, h = p["acoplamiento"], p["conductancia"]
    alfa = g / cc + (g + h) / cd
    beta = g * h / (cc * cd)
    discriminante = (g / cc - (g + h) / cd) ** 2 + 4 * g * g / (cc * cd)
    raiz_rapida = (-alfa - sqrt(discriminante)) / 2
    # El producto de las dos raíces es beta. Esta división evita cancelaciones.
    raiz_lenta = beta / raiz_rapida
    equilibrio_c = p["ambiente"] + p["potencia"] / h + p["potencia"] / g
    equilibrio_d = p["ambiente"] + p["potencia"] / h
    velocidad = (p["potencia"] - g * (p["inicial_c"] - p["inicial_d"])) / cc
    diferencia = p["inicial_c"] - equilibrio_c
    a = (velocidad - raiz_rapida * diferencia) / (raiz_lenta - raiz_rapida)
    b = diferencia - a
    return dict(alfa=alfa, beta=beta, q=(g + h) * p["potencia"] / (cc * cd),
                raiz_lenta=raiz_lenta, raiz_rapida=raiz_rapida,
                A=a, B=b, velocidad_inicial=velocidad,
                equilibrio_c=equilibrio_c, equilibrio_d=equilibrio_d)


def solucion_analitica(tiempo, p, datos=None):
    """Evalúa las dos temperaturas mediante la solución exponencial."""
    if not isinstance(tiempo, (int, float)) or not isfinite(tiempo) or tiempo < 0:
        raise ValueError("El tiempo debe ser finito y mayor o igual a cero.")
    d = datos if datos is not None else caracterizar(p)
    termino_lento = d["A"] * exp(d["raiz_lenta"] * tiempo)
    termino_rapido = d["B"] * exp(d["raiz_rapida"] * tiempo)
    tc = d["equilibrio_c"] + termino_lento + termino_rapido
    derivada = d["raiz_lenta"] * termino_lento + d["raiz_rapida"] * termino_rapido
    td = tc + p["capacidad_c"] * derivada / p["acoplamiento"] - p["potencia"] / p["acoplamiento"]
    if tiempo == 0:
        return p["inicial_c"], p["inicial_d"]
    return tc, td


def pendientes(tc, td, p):
    """Calcula ambas derivadas desde el mismo par de temperaturas."""
    intercambio = p["acoplamiento"] * (tc - td)
    perdida = p["conductancia"] * (td - p["ambiente"])
    derivada_c = (p["potencia"] - intercambio) / p["capacidad_c"]
    derivada_d = (intercambio - perdida) / p["capacidad_d"]
    return derivada_c, derivada_d


def resolver_euler(tiempos, p):
    temperaturas = [(p["inicial_c"], p["inicial_d"])]
    for indice in range(1, len(tiempos)):
        paso = tiempos[indice] - tiempos[indice - 1]
        tc, td = temperaturas[-1]
        derivada_c, derivada_d = pendientes(tc, td, p)
        nueva_c = tc + paso * derivada_c
        nueva_d = td + paso * derivada_d
        temperaturas.append((nueva_c, nueva_d))
    return temperaturas


def resolver_heun(tiempos, p):
    """Predicción de Euler y corrección con el promedio de dos pendientes."""
    temperaturas = [(p["inicial_c"], p["inicial_d"])]
    for indice in range(1, len(tiempos)):
        paso = tiempos[indice] - tiempos[indice - 1]
        tc, td = temperaturas[-1]
        inicio_c, inicio_d = pendientes(tc, td, p)
        prediccion_c = tc + paso * inicio_c
        prediccion_d = td + paso * inicio_d
        final_c, final_d = pendientes(prediccion_c, prediccion_d, p)
        nueva_c = tc + paso * (inicio_c + final_c) / 2
        nueva_d = td + paso * (inicio_d + final_d) / 2
        temperaturas.append((nueva_c, nueva_d))
    return temperaturas


def simular(p):
    datos = caracterizar(p)
    cociente = p["duracion"] / p["paso_solicitado"]
    entero = round(cociente)
    cantidad = max(1, entero if isclose(cociente, entero, rel_tol=1e-13, abs_tol=1e-13) else ceil(cociente))
    if cantidad > 20000:
        raise ValueError("La simulación supera 20 000 intervalos. Aumenta el paso o reduce la duración.")
    paso = p["duracion"] / cantidad
    limite = 2 / abs(datos["raiz_rapida"])
    if paso >= limite:
        raise ValueError(f"El paso es demasiado grande para estos parámetros. Debe ser menor que {limite:.6g} s.")
    tiempos = [indice * paso for indice in range(cantidad + 1)]
    tiempos[-1] = p["duracion"]
    exactas = [solucion_analitica(t, p, datos) for t in tiempos]
    series = {"Euler": resolver_euler(tiempos, p), "Heun": resolver_heun(tiempos, p)}
    errores, resumen = {}, {}
    for metodo in METODOS:
        errores[metodo] = []
        for aproximacion, exacta in zip(series[metodo], exactas):
            errores[metodo].append((abs(aproximacion[0] - exacta[0]),
                                    abs(aproximacion[1] - exacta[1])))
        resumen[metodo] = dict(error_c=max(e[0] for e in errores[metodo]),
                               error_d=max(e[1] for e in errores[metodo]))
    return dict(parametros=dict(p), datos=datos, tiempos=tiempos, paso=paso,
                exactas=exactas, series=series, errores=errores, resumen=resumen)


def estudiar_paso(base):
    """Compara la precisión del caso base con tres mallas sucesivas."""
    filas = []
    for factor in (1, 2, 4):
        if (len(base["tiempos"]) - 1) * factor > 20000:
            break
        p = dict(base["parametros"], paso_solicitado=base["paso"] / factor)
        r = base if factor == 1 else simular(p)
        fila = {"Paso (s)": r["paso"]}
        for metodo in METODOS:
            fila[NOMBRES[metodo] + " (°C)"] = max(r["resumen"][metodo].values())
        filas.append(fila)
    return filas


def energia_exacta(tiempo, p, datos=None):
    """Energía ingresada, almacenada y cedida al ambiente, en J."""
    d = datos if datos is not None else caracterizar(p)
    tc, td = solucion_analitica(tiempo, p, d)
    almacenada = p["capacidad_c"] * (tc - p["inicial_c"]) + p["capacidad_d"] * (td - p["inicial_d"])
    integral = (d["equilibrio_d"] - p["ambiente"]) * tiempo
    for coeficiente, raiz in ((d["A"], d["raiz_lenta"]), (d["B"], d["raiz_rapida"])):
        integral += coeficiente * (1 + p["capacidad_c"] * raiz / p["acoplamiento"]) * expm1(raiz * tiempo) / raiz
    disipada = p["conductancia"] * integral
    ingresada = p["potencia"] * tiempo
    return dict(ingresada=ingresada, almacenada=almacenada, disipada=disipada,
                residuo=ingresada - almacenada - disipada)
