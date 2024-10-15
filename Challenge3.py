import yfinance as yf    
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from ETFS import instrumentos_financieros

# Función para obtener rendimiento histórico aritmético
def obtener_rendimiento_aritmetico(instrumento, inicio, fin):
    try:
        datos = yf.download(instrumento["simbolo"], start=inicio, end=fin)
        if datos.empty:
            st.warning(f"No se encontraron datos para el símbolo {instrumento['simbolo']}.")
            return None, None
        if 'Adj Close' not in datos.columns:
            st.warning(f"La columna 'Adj Close' no está disponible para el símbolo {instrumento['simbolo']}.")
            return None, None
        
        precios = datos['Adj Close'].copy()

        # Verificar si hay valores nulos y eliminarlos
        precios = precios.dropna()
        if precios.empty:
            st.warning(f"No se encontraron precios válidos para {instrumento['simbolo']}.")
            return None, None

        # Calcular los rendimientos diarios
        datos['Rendimientos'] = precios.pct_change()
        
        # Si los rendimientos están vacíos o no se pueden calcular
        if datos['Rendimientos'].isnull().all():
            st.warning(f"No se pudieron calcular rendimientos para el símbolo {instrumento['simbolo']}.")
            return None, None
        
        rendimiento_promedio_diario = datos['Rendimientos'].mean()
        
        return rendimiento_promedio_diario, precios
    except KeyError:
        st.error(f"Error: El símbolo '{instrumento['simbolo']}' no es válido.")
        return None, None
    except Exception as e:
        st.error(f"Ocurrió un error: {str(e)}")
        return None, None

# Función para calcular rendimiento anualizado
def calcular_rendimiento_anualizado(rendimiento_diario_promedio, horizonte_inversion):
    dias_por_anio = 252
    rendimiento_anualizado = ((1 + rendimiento_diario_promedio) ** dias_por_anio - 1) * 100
    return rendimiento_anualizado

# Función para calcular capital final
def calcular_capital_final(capital_inicial, rendimiento_anualizado, horizonte_inversion):
    capital_final = capital_inicial * ((1 + (rendimiento_anualizado / 100)) ** horizonte_inversion)
    return capital_final

# Aplicación en Streamlit
st.title("Simulador OptiMaxx Patrimonial")

# 1. Ingresar capital con formato de miles y millones
capital_minimo = 500000
capital = st.number_input("Ingrese el capital a invertir (mínimo $500,000 pesos):", min_value=capital_minimo, value=capital_minimo, step=100000)
capital_format = "${:,.0f}".format(float(capital))
st.write(f"**Capital ingresado**: {capital_format}")

# 2. Seleccionar horizonte de inversión entre 1 y 10 años
horizonte_inversion = st.selectbox("Seleccione el horizonte de inversión (en años):", options=list(range(1, 11)))

# Seleccionar instrumentos financieros desde el archivo ETFS.py
nombres_instrumentos = [instrumento["nombre"] for instrumento in instrumentos_financieros]
seleccionados = st.multiselect("Seleccione uno o más instrumentos financieros:", options=nombres_instrumentos)

# Fecha de inicio y fin para calcular rendimiento
fecha_fin = "2024-10-01"
fecha_inicio = f"{2024 - horizonte_inversion}-01-01"

# Botón para calcular
if st.button("Calcular"):
    if seleccionados:
        rendimiento_total_portafolio = 0
        precios_historicos = {}
        rendimientos_anualizados = []
        
        st.write("Detalles de la inversión:")

        # Calcular rendimiento para cada instrumento seleccionado
        for instrumento in instrumentos_financieros:
            if instrumento["nombre"] in seleccionados:
                rendimiento_diario, precios = obtener_rendimiento_aritmetico(instrumento, fecha_inicio, fecha_fin)
                if rendimiento_diario is not None:
                    rendimiento_anualizado = calcular_rendimiento_anualizado(rendimiento_diario, horizonte_inversion)

                    # Calcular el porcentaje invertido en cada instrumento
                    porcentaje_invertido = 100 / len(seleccionados)  # Cada instrumento recibe un porcentaje igual
                    
                    # Mostrar información del instrumento
                    st.write(f"**Instrumento**: {instrumento['nombre']}")
                    st.write(f"**Descripción**: {instrumento['descripcion']}")
                    st.write(f"**Símbolo**: {instrumento['simbolo']}")
                    st.write(f"**Porcentaje Invertido**: {porcentaje_invertido:.2f}%")
                    st.write(f"**Rendimiento Anualizado**: {rendimiento_anualizado:.2f}%")
                    st.write("---")
                    
                    # Almacenar los precios históricos ajustados para el gráfico
                    precios_historicos[instrumento["nombre"]] = precios
                    
                    # Guardar rendimientos para calcular el rendimiento total del portafolio
                    rendimientos_anualizados.append(rendimiento_anualizado)

        # Comprobar si se han calculado rendimientos
        if rendimientos_anualizados:
            # Calcular el rendimiento promedio del portafolio
            rendimiento_anualizado_portafolio = sum(rendimientos_anualizados) / len(rendimientos_anualizados)

            # Calcular capital final
            capital_final = calcular_capital_final(capital, rendimiento_anualizado_portafolio, horizonte_inversion)

            # Mostrar rendimiento del portafolio
            st.write("**Rendimiento del Portafolio**:")
            st.write(f"**Rendimiento Anualizado Promedio**: {rendimiento_anualizado_portafolio:.2f}%")
            st.write(f"**Capital Final Estimado**: ${capital_final:,.2f}")

            # 3. Graficar la tendencia del rendimiento para cada instrumento
            st.write("**Gráfico de Tendencia de los Instrumentos Seleccionados**:")
            fig, ax = plt.subplots(figsize=(10, 4))  # Tamaño ajustado del gráfico

            for nombre, precios in precios_historicos.items():
                # Calcular rendimiento relativo al primer día
                rendimiento_relativo = (precios / precios.iloc[0]) * 100
                ax.plot(rendimiento_relativo.index, rendimiento_relativo, label=nombre)

            ax.set_xlabel("Fecha")
            ax.set_ylabel("Rendimiento (%)")
            ax.set_title("Tendencia de Rendimiento Relativo (Base 100)")
            ax.legend(loc="upper left")
            st.pyplot(fig)
        else:
            st.warning("No se pudo calcular el rendimiento del portafolio debido a que no hay datos válidos.")
    else:
        st.write("No se ha seleccionado ningún instrumento.")
