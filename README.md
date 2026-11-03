# CORE ΔT

Simulación de la temperatura de un procesador y su disipador. Compara la solución analítica con Euler y Euler mejorado de Heun, y estudia tres escenarios térmicos.

## Ejecución

Requiere Python 3.10 o posterior. Desde la carpeta que contiene `aplicacion.py`:

```bash
python -m pip install -r requirements.txt
python -m streamlit run aplicacion.py
```

En Windows también se puede utilizar `py` en lugar de `python`, con el mismo intérprete en los dos comandos.

La aplicación muestra una simulación inicial. Las condiciones se introducen en el panel lateral y se aplican con **Simular**. El escenario y el instante de observación se seleccionan sobre los resultados. Las pestañas reúnen la evolución térmica, el desarrollo matemático y las descargas.

## Organización del código

| Archivo | Responsabilidad |
|---|---|
| `modelo.py` | Balance térmico, fórmula analítica, Euler, Euler mejorado y cálculo de errores |
| `aplicacion.py` | Controles, esquema térmico, tablas y descargas |
| `graficas.py` | Representación de temperaturas y errores |
| `exportar.py` | Datos y formato del Excel |
| `generar_resultados.py` | Exportación del ejemplo sin abrir la interfaz |
| `recursos/procesador.svg` | Esquema del procesador y el disipador |

La lógica del cálculo sigue cinco operaciones: recibir parámetros, crear los tiempos, calcular las soluciones, comparar sus valores y exportar las series. Las funciones y las variables propias están en español. El núcleo matemático utiliza solamente la biblioteca estándar `math`.

## Modelo de dos temperaturas

El procesador recibe potencia térmica. El calor pasa al disipador y de este al ambiente. Cada cuerpo tiene una temperatura uniforme; las capacidades, las conductancias, el ambiente y la potencia son constantes dentro de cada escenario.

\[
C_cT_c'=P-g(T_c-T_d),\qquad
C_dT_d'=g(T_c-T_d)-h(T_d-T_a).
\]

| Símbolo | Significado | Unidad |
|---|---|---|
| Tc, Td | Temperaturas del procesador y del disipador | °C |
| Ta | Temperatura ambiental | °C |
| P | Potencia térmica | W |
| Cc, Cd | Capacidades térmicas | J/°C |
| g | Conductancia entre los cuerpos | W/°C |
| h | Conductancia del disipador al ambiente | W/°C |

`pendientes` calcula las dos derivadas desde el mismo par de temperaturas. El calor intercambiado aparece con signos opuestos en los dos balances.

### Ecuación de segundo orden

Al eliminar Td y definir x = Tc − Ta:

\[
x''+\alpha x'+\beta x=q,
\quad \alpha=\frac{g}{C_c}+\frac{g+h}{C_d},
\quad \beta=\frac{gh}{C_cC_d},
\quad q=\frac{(g+h)P}{C_cC_d}.
\]

Las dos condiciones iniciales son:

\[
x_0=T_c(0)-T_a,\qquad v_0=x'(0)=\frac{P-g[T_c(0)-T_d(0)]}{C_c}.
\]

Es una EDO lineal de segundo orden con coeficientes constantes. Para P positiva es no homogénea. El sistema de dos balances es la forma equivalente utilizada por los métodos numéricos.

### Solución analítica

La transformada de Laplace conduce a:

\[
X(s)=\frac{s x_0+v_0+\alpha x_0+q/s}{s^2+\alpha s+\beta}.
\]

Con las dos raíces de la ecuación característica y el exceso de equilibrio:

\[
\lambda_{1,2}=\frac{-\alpha\pm\sqrt{\alpha^2-4\beta}}2,
\qquad x_\infty=\frac{q}{\beta},
\]

la descomposición en fracciones parciales es:

\[
X(s)=\frac{x_\infty}{s}+\frac{A}{s-\lambda_1}+\frac{B}{s-\lambda_2},
\]

\[
A=\frac{v_0-\lambda_2(x_0-x_\infty)}{\lambda_1-\lambda_2},
\qquad B=x_0-x_\infty-A.
\]

La transformada inversa da las temperaturas:

\[
T_c(t)=T_a+x_\infty+Ae^{\lambda_1t}+Be^{\lambda_2t},
\qquad T_d(t)=T_c(t)+\frac{C_c}{g}T_c'(t)-\frac{P}{g}.
\]

`caracterizar` calcula los coeficientes y `solucion_analitica` evalúa esta expresión. No se resuelve la transformada nuevamente en cada instante. Las raíces son reales, distintas y negativas para capacidades y conductancias positivas.

Los equilibrios son:

\[
T_{c,\infty}=T_a+\frac P g+\frac P h,\qquad
T_{d,\infty}=T_a+\frac P h.
\]

Las conductancias determinan el equilibrio y las capacidades intervienen en la evolución temporal. Sumar Cc y Cd no hace equivalente este modelo al de una sola temperatura: ahora existe una resistencia térmica interna adicional.

### Euler y Euler mejorado

Euler utiliza la pendiente al comienzo del intervalo:

\[
\mathbf y_{n+1}=\mathbf y_n+\Delta t F(\mathbf y_n),\qquad \mathbf y=(T_c,T_d).
\]

Euler mejorado predice primero las dos temperaturas y calcula otras dos pendientes en la predicción. Después promedia las pendientes iniciales y finales:

\[
\mathbf y^*=\mathbf y_n+\Delta t F(\mathbf y_n),
\]

\[
\mathbf y_{n+1}=\mathbf y_n+\frac{\Delta t}{2}\left[F(\mathbf y_n)+F(\mathbf y^*)\right].
\]

`resolver_euler` y `resolver_heun` realizan estas operaciones en ciclos separados. En cada intervalo se calculan ambas temperaturas desde el estado anterior; ninguna utiliza por error el valor recién actualizado de la otra.

La malla incluye exactamente el inicio y el final. El paso efectivo es la duración dividida entre un número entero de intervalos y no supera el solicitado. La condición de estabilidad para ambos métodos en este modelo es:

\[
\Delta t<\frac{2}{|\lambda_{\mathrm{rápida}}|}.
\]

El programa valida esta condición, entradas finitas, temperaturas admisibles, capacidades y conductancias positivas y un máximo de 20 000 intervalos.

### Comparación

\[
E_c=\max_n|T_{c,n}-T_c(t_n)|,\qquad
E_d=\max_n|T_{d,n}-T_d(t_n)|.
\]

Se utilizan los mismos instantes para las tres soluciones. Los errores son diferencias absolutas en °C, no porcentajes. Los resultados se redondean únicamente al mostrarlos.

## Caso de referencia

| Entrada | Base | Mayor potencia | Mayor disipación |
|---|---:|---:|---:|
| Potencia (W) | 18 | 24 | 18 |
| Conductancia al ambiente (W/°C) | 0,50 | 0,50 | 0,75 |
| Conductancia entre cuerpos (W/°C) | 1 | 1 | 1 |
| Capacidad del procesador (J/°C) | 10 | 10 | 10 |
| Capacidad del disipador (J/°C) | 10 | 10 | 10 |
| Ambiente e iniciales (°C) | 25 | 25 | 25 |
| Duración (s) | 180 | 180 | 180 |
| Paso solicitado (s) | 1 | 1 | 1 |

Cada alternativa modifica una sola entrada. La malla de referencia tiene 181 instantes por escenario.

| Resultado analítico | Base | Mayor potencia | Mayor disipación |
|---|---:|---:|---:|
| Procesador a 180 s (°C) | 78,013886 | 95,685181 | 66,842278 |
| Disipador a 180 s (°C) | 60,230065 | 71,973420 | 48,890699 |
| Equilibrio del procesador (°C) | 79 | 97 | 67 |
| Equilibrio del disipador (°C) | 61 | 73 | 49 |

La mayor potencia eleva las temperaturas y los equilibrios. La mayor conductancia ambiental los reduce. El instante final de una simulación no se identifica con el equilibrio asintótico.

En el caso base, Euler presenta errores máximos de 0,207670904 °C para Tc y 0,161992415 °C para Td. Euler mejorado presenta 0,011681880 °C para Tc y 0,014233158 °C para Td. Comparar ambos componentes evita ocultar un error mayor en el disipador.

La sección de refinamiento repite el caso base reduciendo el paso. La comprobación energética verifica:

\[
Pt=C_c[T_c(t)-T_c(0)]+C_d[T_d(t)-T_d(0)]+\int_0^t h[T_d(u)-T_a]\,du.
\]

## Excel y figuras

El libro tiene dos hojas:

- **Resultados:** escenario, tiempo y las temperaturas analítica, Euler y Euler mejorado de ambos cuerpos. En el ejemplo hay 543 filas de datos.
- **Parámetros:** entradas, paso, instantes, equilibrios, temperaturas finales y errores máximos de cada método y componente.

Los datos del Excel proceden de las mismas series utilizadas por las gráficas. Para recalcular una simulación se cambian las condiciones en la aplicación y se exporta de nuevo. Las celdas conservan la precisión del cálculo y muestran cuatro decimales.

La carpeta `resultados` contiene el Excel, CSV, datos JSON y seis figuras científicas a 300 ppp. Para regenerarlos:

```bash
python generar_resultados.py
```
