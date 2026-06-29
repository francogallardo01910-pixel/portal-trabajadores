import streamlit as st
from supabase import create_client

# -----------------------------------
# CONFIGURACIÓN
# -----------------------------------

st.set_page_config(
    page_title="ALFA Control Portal",
    page_icon="📦",
    layout="centered"
)

# -----------------------------------
# CONEXIÓN SUPABASE
# -----------------------------------

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# -----------------------------------
# TÍTULO
# -----------------------------------

st.title("📦 ALFA Control Portal")

st.subheader("Solicitud mensual de alimento")

st.divider()

# -----------------------------------
# BUSCAR TRABAJADOR
# -----------------------------------

rut = st.text_input(
    "Ingrese su RUT",
    placeholder="Ej: 12345678-9"
)

if rut:

    respuesta = (
        supabase
        .table("trabajadores")
        .select("*")
        .eq("rut", rut)
        .execute()
    )

    if len(respuesta.data) == 0:

        st.error("Trabajador no encontrado")

    else:

        trabajador = respuesta.data[0]

        st.success("Trabajador encontrado")

        st.write("### Nombre")

        st.write(trabajador["nombre"])

        st.write("### Estado")

        if trabajador["activo"]:

            st.success("ACTIVO")

        else:

            st.error("INACTIVO")
