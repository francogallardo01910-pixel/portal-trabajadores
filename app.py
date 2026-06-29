import streamlit as st

st.set_page_config(
    page_title="ALFA Control Portal",
    page_icon="📦",
    layout="centered"
)

st.title("📦 ALFA Control Portal")
st.subheader("Portal del Trabajador")

st.info("Primera versión del portal funcionando correctamente.")

rut = st.text_input("Ingrese su RUT", placeholder="Ej: 12345678-9")

if rut:
    st.success(f"RUT ingresado: {rut}")

    st.write("Aquí después conectaremos con Supabase para buscar el trabajador.")

    producto_1 = st.selectbox(
        "Alimento 1",
        ["Alfa Adulto 25 kg", "Alfa Senior 25 kg", "Alfa Cachorro 20 kg"]
    )

    cantidad_1 = st.number_input(
        "Cantidad alimento 1",
        min_value=1,
        max_value=3,
        step=1
    )

    if st.button("Enviar solicitud"):
        st.success("Solicitud registrada en modo prueba.")
        st.write("Producto:", producto_1)
        st.write("Cantidad:", cantidad_1)
