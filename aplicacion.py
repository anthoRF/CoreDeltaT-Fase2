"""CORE ΔT. Ejecutar con: python -m streamlit run aplicacion.py"""
from html import escape
from pathlib import Path
import streamlit as st
from exportar import crear_excel, preparar_tabla
from graficas import (comparar_metodos, comparar_escenarios, comparar_temperaturas,
                       comparar_errores, guardar_grafica)
from modelo import (METODOS, NOMBRES, construir_escenarios, simular,
                    estudiar_paso, solucion_analitica, energia_exacta)


@st.cache_data(show_spinner=False, max_entries=3)
def calcular(entradas):
    resultados = [simular(p) for p in entradas]
    return resultados, crear_excel(resultados)


def dibujar_procesador(tc, td, p, tiempo):
    dibujo = (Path(__file__).parent / "recursos/procesador.svg").read_text(encoding="utf-8")
    intercambio = p["acoplamiento"] * (tc - td)
    perdida = p["conductancia"] * (td - p["ambiente"])

    def flecha(valor, inicio, fin):
        if abs(valor) < 1e-10:
            return ""
        return f"M{inicio} 148 H{fin}" if valor > 0 else f"M{fin} 148 H{inicio}"

    valores = {"TC": f"{tc:.2f}", "TD": f"{td:.2f}",
               "TAMANO_C": "29" if abs(tc) < 1000 else "21",
               "TAMANO_D": "29" if abs(td) < 1000 else "21",
               "POTENCIA": f"{p['potencia']:g}", "AMBIENTE": f"{p['ambiente']:g}",
               "CALOR_G": f"{abs(intercambio):.2f}", "CALOR_H": f"{abs(perdida):.2f}",
               "FLUJO_G": flecha(intercambio, 410, 548),
               "FLUJO_H": flecha(perdida, 800, 1010),
               "ENTRADA": flecha(p["potencia"], 20, 148),
               "ETIQUETA_H": "AL AMBIENTE" if perdida >= 0 else "DEL AMBIENTE",
               "ESCENARIO": escape(p["nombre"]), "TIEMPO": f"{tiempo:.2f}"}
    for nombre, valor in valores.items():
        dibujo = dibujo.replace("{{" + nombre + "}}", valor)
    st.image(dibujo, width="stretch")


st.set_page_config(page_title="CORE ΔT", layout="wide")
st.markdown("""
<style>
.stApp {background:#fff;color:#17304f;font-family:Arial,sans-serif}
.block-container {max-width:1460px;padding-top:2rem;padding-bottom:2rem}
[data-testid="stSidebar"] {background:#f4f6f5;border-right:1px solid #dde4e0}
[data-testid="stSidebar"] .block-container {padding-top:1.2rem}
h1,h2,h3 {font-family:Arial,sans-serif;font-weight:600;letter-spacing:-.025em}
h1 {font-size:2.6rem !important;padding-bottom:.15rem !important}
h3 {font-size:1.2rem !important}
.stButton button,.stDownloadButton button {border-radius:3px;box-shadow:none}
[data-testid="stToolbar"] {display:none}
[data-testid="stMetric"] {border:0;background:transparent;box-shadow:none}
.encabezado {border-bottom:1px solid #cbd7d0;padding-bottom:1rem;margin-bottom:1.1rem}
.encabezado p {font-size:1rem;color:#596c64;margin:0}
.encabezado h1 span {color:#205847}
@media(max-width:700px){.block-container{padding-top:4rem}h1{font-size:2.1rem !important}}
</style>
<div class="encabezado"><h1>CORE <span>ΔT</span></h1>
<p>Respuesta térmica de un procesador y su disipador</p></div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("Condiciones")
    with st.form("condiciones", border=False):
        st.markdown("**Potencia**")
        potencia_base = st.number_input("Base P (W)", 0.0, 500.0, 18.0, 1.0, key="potencia_base")
        potencia_alternativa = st.number_input("Alternativa P (W)", 0.0, 500.0, 24.0, 1.0, key="potencia_alternativa")
        st.markdown("**Disipación al ambiente**")
        conductancia = st.number_input("Base h (W/°C)", 0.01, 10.0, 0.5, 0.05, format="%.2f", key="conductancia")
        conductancia_alternativa = st.number_input("Alternativa h (W/°C)", 0.01, 10.0, 0.75, 0.05, format="%.2f", key="conductancia_alternativa")
        st.markdown("**Tiempo**")
        duracion = st.number_input("Duración (s)", 1.0, 3600.0, 180.0, 10.0, key="duracion")
        paso = st.number_input("Paso Δt (s)", 0.01, 60.0, 1.0, 0.1, format="%.3f", key="paso")
        with st.expander("Temperaturas y propiedades"):
            ambiente = st.number_input("Ambiente Ta (°C)", -50.0, 150.0, 25.0, 1.0, key="ambiente")
            inicial_c = st.number_input("Inicial del procesador Tc (°C)", -50.0, 250.0, 25.0, 1.0, key="inicial_c")
            inicial_d = st.number_input("Inicial del disipador Td (°C)", -50.0, 250.0, 25.0, 1.0, key="inicial_d")
            capacidad_c = st.number_input("Capacidad Cc (J/°C)", 1.0, 1000.0, 10.0, 1.0, key="capacidad_c")
            capacidad_d = st.number_input("Capacidad Cd (J/°C)", 1.0, 1000.0, 10.0, 1.0, key="capacidad_d")
            acoplamiento = st.number_input("Conductancia entre cuerpos g (W/°C)", 0.01, 10.0, 1.0, 0.05, format="%.2f", key="acoplamiento")
        ejecutar = st.form_submit_button("Simular", type="primary", width="stretch")

if ejecutar or "resultados" not in st.session_state:
    try:
        comunes = dict(ambiente=ambiente, inicial_c=inicial_c, inicial_d=inicial_d,
                       capacidad_c=capacidad_c, capacidad_d=capacidad_d,
                       acoplamiento=acoplamiento, duracion=duracion, paso_solicitado=paso)
        entradas = construir_escenarios(comunes, potencia_base, potencia_alternativa,
                                        conductancia, conductancia_alternativa)
        st.session_state.resultados, st.session_state.excel = calcular(entradas)
        st.session_state.error = ""
    except (ValueError, OverflowError, ZeroDivisionError) as error:
        st.session_state.error = str(error)

if st.session_state.get("error"):
    st.error(st.session_state.error)
    st.stop()

resultados = st.session_state.resultados
nombres = [r["parametros"]["nombre"] for r in resultados]
escenario = st.radio("Escenario", nombres, horizontal=True)
r = resultados[nombres.index(escenario)]
p, d = r["parametros"], r["datos"]
tf = p["duracion"]
evolucion, fundamentos, datos = st.tabs(["Evolución térmica", "Modelo y métodos", "Resultados"])

with evolucion:
    izquierda, derecha = st.columns([2.15, 1], gap="large")
    with izquierda:
        if "instante" not in st.session_state:
            st.session_state.instante = tf
        st.session_state.instante = min(tf, max(0.0, st.session_state.instante))
        tiempo = st.slider("Instante de observación (s)", 0.0, tf, step=tf / 100,
                           key="instante", format="%.2f")
        tc, td = solucion_analitica(tiempo, p, d)
        dibujar_procesador(tc, td, p, tiempo)
        st.caption(f"Tc = {tc:.2f} °C · Td = {td:.2f} °C · t = {tiempo:.2f} s")
    with derecha:
        st.subheader(f"Temperaturas a {tf:g} s")
        st.dataframe([{"Escenario": rr["parametros"]["nombre"],
                       "Tc (°C)": rr["exactas"][-1][0], "Td (°C)": rr["exactas"][-1][1]}
                      for rr in resultados], hide_index=True, width="stretch",
                     column_config={c: st.column_config.NumberColumn(format="%.4f") for c in ("Tc (°C)", "Td (°C)")})
        st.caption("Tc: procesador · Td: disipador")
        st.caption(f"Δt = {r['paso']:.6g} s · {len(r['tiempos']) - 1} intervalos")

    componente = st.radio("Temperatura", ["Procesador", "Disipador"], horizontal=True)
    j = 0 if componente == "Procesador" else 1
    fig_metodos = comparar_metodos(r, j)
    fig_escenarios = comparar_escenarios(resultados, j)
    fig_temperaturas = comparar_temperaturas(r)
    fig_errores = comparar_errores(r)
    izquierda, derecha = st.columns(2, gap="large")
    with izquierda:
        st.subheader("Solución analítica, Euler y Euler mejorado")
        st.pyplot(fig_metodos, width="stretch")
        st.caption(f"{escenario} · {componente}")
    with derecha:
        st.subheader("Comparación de escenarios")
        st.pyplot(fig_escenarios, width="stretch")
        st.caption(f"{componente} · solución analítica")
    with izquierda:
        st.subheader("Procesador y disipador")
        st.pyplot(fig_temperaturas, width="stretch")
        st.caption("Líneas punteadas: temperaturas de equilibrio.")
    with derecha:
        st.subheader("Error de los métodos")
        st.pyplot(fig_errores, width="stretch")
        st.caption("Mayor error absoluto entre Tc y Td en cada instante.")

    st.subheader(f"Errores máximos · {escenario}")
    st.dataframe([{"Método": NOMBRES[m], "Tc (°C)": r["resumen"][m]["error_c"],
                   "Td (°C)": r["resumen"][m]["error_d"]} for m in METODOS],
                 hide_index=True, width="stretch", column_config={
                     c: st.column_config.NumberColumn(format="%.6f") for c in ("Tc (°C)", "Td (°C)")})
    base, alternativa_p, alternativa_h = resultados
    diferencia_p = alternativa_p["exactas"][-1][0] - base["exactas"][-1][0]
    diferencia_h = alternativa_h["exactas"][-1][0] - base["exactas"][-1][0]
    st.write(f"A {tf:g} s, la alternativa de potencia presenta una diferencia de {diferencia_p:+.4f} °C "
             f"en el procesador respecto de la base; la alternativa de disipación, {diferencia_h:+.4f} °C.")

with fundamentos:
    st.subheader("Balance térmico")
    st.write("El procesador recibe potencia térmica y transfiere calor al disipador. "
             "El disipador almacena parte de esa energía y cede calor al ambiente.")
    st.latex(r"C_c\frac{dT_c}{dt}=P-g(T_c-T_d)")
    st.latex(r"C_d\frac{dT_d}{dt}=g(T_c-T_d)-h(T_d-T_a)")
    st.dataframe([{"Símbolo": s, "Magnitud": n, "Valor": v, "Unidad": u} for s, n, v, u in [
        ("P", "Potencia térmica", p["potencia"], "W"),
        ("Cc", "Capacidad del procesador", p["capacidad_c"], "J/°C"),
        ("Cd", "Capacidad del disipador", p["capacidad_d"], "J/°C"),
        ("g", "Conductancia entre cuerpos", p["acoplamiento"], "W/°C"),
        ("h", "Conductancia al ambiente", p["conductancia"], "W/°C"),
        ("Ta", "Temperatura ambiental", p["ambiente"], "°C")]], hide_index=True, width="stretch")
    st.write("Cada cuerpo se representa con una temperatura uniforme. La potencia, el ambiente, "
             "las capacidades y las conductancias permanecen constantes durante cada escenario.")
    with st.expander("Ecuación de segundo orden"):
        st.write("Al eliminar la temperatura del disipador y definir el exceso térmico x:")
        st.latex(r"x=T_c-T_a,\qquad x''+\alpha x'+\beta x=q")
        st.latex(r"\alpha=\frac{g}{C_c}+\frac{g+h}{C_d},\qquad \beta=\frac{gh}{C_c C_d},\qquad q=\frac{(g+h)P}{C_c C_d}")
        st.latex(r"x_0=T_c(0)-T_a,\qquad v_0=x'(0)=\frac{P-g[T_c(0)-T_d(0)]}{C_c}")
        st.write("EDO lineal de segundo orden, con coeficientes constantes. Para potencia positiva, "
                 "su término independiente es distinto de cero.")
        st.write(f"{escenario}: α = {d['alfa']:.6g} s⁻¹; β = {d['beta']:.6g} s⁻²; q = {d['q']:.6g} °C/s².")
    with st.expander("Solución analítica por Laplace"):
        st.markdown("**1. Transformada y condiciones iniciales**")
        st.latex(r"(s^2+\alpha s+\beta)X(s)=s x_0+v_0+\alpha x_0+\frac{q}{s}")
        st.markdown("**2. Raíces y equilibrio**")
        st.latex(r"\lambda_{1,2}=\frac{-\alpha\pm\sqrt{\alpha^2-4\beta}}{2},\qquad x_\infty=\frac{q}{\beta}=\frac{P}{g}+\frac{P}{h}")
        st.markdown("**3. Fracciones parciales**")
        st.latex(r"X(s)=\frac{x_\infty}{s}+\frac{A}{s-\lambda_1}+\frac{B}{s-\lambda_2}")
        st.latex(r"A=\frac{v_0-\lambda_2(x_0-x_\infty)}{\lambda_1-\lambda_2},\qquad B=x_0-x_\infty-A")
        st.markdown("**4. Temperaturas en función del tiempo**")
        st.latex(r"T_c(t)=T_a+x_\infty+A e^{\lambda_1 t}+B e^{\lambda_2 t}")
        st.latex(r"T_d(t)=T_c(t)+\frac{C_c}{g}T_c'(t)-\frac{P}{g}")
        st.write("Las dos raíces son negativas. Los términos exponenciales decaen y las temperaturas se acercan a sus equilibrios.")
        st.latex(r"T_{c,\infty}=T_a+\frac{P}{g}+\frac{P}{h},\qquad T_{d,\infty}=T_a+\frac{P}{h}")
    with st.expander("Euler y Euler mejorado"):
        st.write("El estado contiene las dos temperaturas. F calcula las dos pendientes desde ese mismo estado.")
        st.latex(r"\mathbf y=(T_c,T_d),\qquad F=(F_c,F_d)")
        st.latex(r"F_c=\frac{P-g(T_c-T_d)}{C_c}")
        st.latex(r"F_d=\frac{g(T_c-T_d)-h(T_d-T_a)}{C_d}")
        st.markdown("**Euler: una pendiente por intervalo**")
        st.latex(r"\mathbf y_{n+1}=\mathbf y_n+\Delta t\,F(\mathbf y_n)")
        st.markdown("**Euler mejorado: predecir y promediar dos pendientes**")
        st.latex(r"\mathbf y^*=\mathbf y_n+\Delta t\,F(\mathbf y_n)")
        st.latex(r"\mathbf y_{n+1}=\mathbf y_n+\frac{\Delta t}{2}\left[F(\mathbf y_n)+F(\mathbf y^*)\right]")
        st.write("La predicción se hace para ambos cuerpos antes de calcular la segunda pendiente.")
        st.latex(r"E_c=\max_n|T_{c,n}-T_c(t_n)|,\qquad E_d=\max_n|T_{d,n}-T_d(t_n)|")
        st.write("Los errores máximos se calculan sobre todos los instantes de la simulación.")
    with st.expander("Precisión al reducir el paso · caso base"):
        st.dataframe(estudiar_paso(resultados[0]), hide_index=True, width="stretch", column_config={
            c: st.column_config.NumberColumn(format="%.8f") for c in ("Euler (°C)", "Euler mejorado (°C)")})
        st.caption("Error máximo entre las dos temperaturas, calculado de nuevo para cada malla.")
    with st.expander("Balance de energía"):
        st.latex(r"\Delta U=C_c[T_c(t)-T_c(0)]+C_d[T_d(t)-T_d(0)]")
        st.latex(r"Q_a(t)=\int_0^t h[T_d(u)-T_a]\,du,\qquad Pt=\Delta U+Q_a(t)")
        filas = []
        for rr in resultados:
            e = energia_exacta(tf, rr["parametros"], rr["datos"])
            filas.append({"Escenario": rr["parametros"]["nombre"], "Ingresada (J)": e["ingresada"],
                          "Almacenada (J)": e["almacenada"], "Neta al ambiente (J)": e["disipada"]})
        st.dataframe(filas, hide_index=True, width="stretch", column_config={
            c: st.column_config.NumberColumn(format="%.4f")
            for c in ("Ingresada (J)", "Almacenada (J)", "Neta al ambiente (J)")})

with datos:
    st.subheader("Resultados de los tres escenarios")
    tabla = preparar_tabla(resultados)
    st.dataframe(tabla, hide_index=True, width="stretch", height=360,
                 column_config={c: st.column_config.NumberColumn(format="%.4f") for c in tabla[0] if c != "Escenario"})
    st.download_button("Descargar Excel", st.session_state.excel, "CORE_DeltaT_Fase2_Resultados.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       type="primary", width="stretch")
    st.subheader("Gráficas")
    columnas = st.columns(2)
    for i, (etiqueta, figura, archivo) in enumerate([
        ("Métodos · " + componente, fig_metodos, "metodos"),
        ("Escenarios · " + componente, fig_escenarios, "escenarios"),
        ("Procesador y disipador · " + escenario, fig_temperaturas, "temperaturas"),
        ("Errores · " + escenario, fig_errores, "errores")]):
        columnas[i % 2].download_button(etiqueta, guardar_grafica(figura),
                                        f"CORE_DeltaT_{archivo}.png", mime="image/png", width="stretch")
