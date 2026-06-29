from datetime import datetime
from io import BytesIO

import pandas as pd
import streamlit as st
from supabase import create_client

st.set_page_config(
    page_title="Portal Trabajadores ALFA Control",
    page_icon="📦",
    layout="centered",
)

# =============================
# CONFIGURACIÓN
# =============================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "1234")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =============================
# ESTILOS
# =============================
st.markdown(
    """
    <style>
    .main { background-color: #f7faf8; }
    .block-container { padding-top: 1.5rem; max-width: 760px; }
    .titulo { text-align:center; color:#166534; font-size:34px; font-weight:800; }
    .subtitulo { text-align:center; color:#475569; font-size:17px; margin-bottom:20px; }
    .card { background:white; padding:20px; border-radius:18px; box-shadow:0 2px 12px rgba(0,0,0,0.08); margin-bottom:15px; }
    .ok { color:#166534; font-weight:700; }
    .warn { color:#b45309; font-weight:700; }
    </style>
    """,
    unsafe_allow_html=True,
)

# =============================
# FUNCIONES
# =============================
def mes_actual() -> str:
    return datetime.now().strftime("%Y-%m")


def solicitudes_abiertas() -> bool:
    return datetime.now().day <= 10


def obtener_trabajador(rut: str):
    resp = (
        supabase.table("trabajadores")
        .select("*")
        .eq("rut", rut)
        .eq("activo", True)
        .execute()
    )
    return resp.data[0] if resp.data else None


def obtener_productos():
    resp = (
        supabase.table("productos_alimento")
        .select("*")
        .eq("activo", True)
        .execute()
    )
    productos = []
    for p in resp.data:
        producto = str(p.get("producto") or "").strip()
        formato = str(p.get("formato") or "").strip()
        nombre = f"{producto} {formato}".strip()
        if nombre:
            productos.append(nombre)
    return productos


def ya_solicito(rut: str, mes: str) -> bool:
    resp = (
        supabase.table("solicitudes_alimento")
        .select("id")
        .eq("rut", rut)
        .eq("mes", mes)
        .execute()
    )
    return bool(resp.data)


def insertar_solicitud(nombre: str, rut: str, items: list[dict]):
    data = {
        "mes": mes_actual(),
        "rut": rut,
        "nombre": nombre,
        "estado": "Pendiente",
        "producto_1": items[0]["producto"] if len(items) > 0 else None,
        "cantidad_1": items[0]["cantidad"] if len(items) > 0 else None,
        "producto_2": items[1]["producto"] if len(items) > 1 else None,
        "cantidad_2": items[1]["cantidad"] if len(items) > 1 else None,
        "producto_3": items[2]["producto"] if len(items) > 2 else None,
        "cantidad_3": items[2]["cantidad"] if len(items) > 2 else None,
    }
    return supabase.table("solicitudes_alimento").insert(data).execute()


def obtener_solicitudes():
    resp = (
        supabase.table("solicitudes_alimento")
        .select("*")
        .order("fecha", desc=True)
        .execute()
    )
    return resp.data or []


def df_resumen_productos(df: pd.DataFrame) -> pd.DataFrame:
    filas = []
    for _, r in df.iterrows():
        for i in [1, 2, 3]:
            prod = r.get(f"producto_{i}")
            cant = r.get(f"cantidad_{i}")
            if pd.notna(prod) and prod and pd.notna(cant):
                filas.append({"Producto": prod, "Cantidad": int(cant)})
    if not filas:
        return pd.DataFrame(columns=["Producto", "Total solicitado"])
    tmp = pd.DataFrame(filas)
    return tmp.groupby("Producto", as_index=False)["Cantidad"].sum().rename(columns={"Cantidad": "Total solicitado"})


def crear_excel(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Solicitudes")
        resumen = df_resumen_productos(df)
        resumen.to_excel(writer, index=False, sheet_name="Resumen productos")
    output.seek(0)
    return output.read()

# =============================
# ENCABEZADO
# =============================
st.markdown('<div class="titulo">ALFA Control Portal</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitulo">Solicitud mensual de alimento para trabajadores</div>', unsafe_allow_html=True)

menu = st.sidebar.radio("Menú", ["Trabajador", "Administrador"])

# =============================
# PORTAL TRABAJADOR
# =============================
if menu == "Trabajador":
    st.info("Las solicitudes se reciben del día 1 al día 10. El retiro será el día 15.")

    if not solicitudes_abiertas():
        st.warning("Las solicitudes de este mes ya fueron cerradas. Consulte nuevamente el próximo mes.")
        st.stop()

    rut = st.text_input("Ingrese su RUT", placeholder="Ej: 12345678-9").strip()

    if rut:
        trabajador = obtener_trabajador(rut)
        if not trabajador:
            st.error("RUT no encontrado o trabajador inactivo.")
            st.stop()

        nombre = trabajador.get("nombre", "")
        st.success(f"Bienvenido/a: {nombre}")

        if ya_solicito(rut, mes_actual()):
            st.warning("Usted ya realizó su solicitud este mes.")
            st.stop()

        productos = obtener_productos()
        if not productos:
            st.error("No hay productos activos cargados. Revise Supabase.")
            st.stop()

        cantidad_alimentos = st.selectbox("¿Cuántos alimentos quiere solicitar?", [1, 2, 3])

        items = []
        for i in range(1, cantidad_alimentos + 1):
            st.markdown(f"### Alimento {i}")
            producto = st.selectbox(f"Producto {i}", productos, key=f"producto_{i}")
            cantidad = st.number_input(
                f"Cantidad {i} (máximo 3 sacos)",
                min_value=1,
                max_value=3,
                step=1,
                key=f"cantidad_{i}",
            )
            items.append({"producto": producto, "cantidad": int(cantidad)})

        confirmar = st.checkbox("Confirmo que los datos ingresados son correctos")

        if st.button("Enviar solicitud", type="primary"):
            if not confirmar:
                st.error("Debe confirmar los datos antes de enviar.")
            else:
                insertar_solicitud(nombre, rut, items)
                st.success("Solicitud enviada correctamente. Retiro programado para el día 15.")
                st.balloons()

# =============================
# PANEL ADMINISTRADOR
# =============================
if menu == "Administrador":
    st.subheader("Panel administrador")
    clave = st.text_input("Clave administrador", type="password")

    if clave != ADMIN_PASSWORD:
        st.info("Ingrese la clave para ver las solicitudes.")
        st.stop()

    datos = obtener_solicitudes()
    if not datos:
        st.warning("Todavía no hay solicitudes registradas.")
        st.stop()

    df = pd.DataFrame(datos)

    meses = sorted(df["mes"].dropna().unique().tolist(), reverse=True)
    mes_sel = st.selectbox("Filtrar por mes", meses)
    df_filtrado = df[df["mes"] == mes_sel].copy()

    st.metric("Solicitudes", len(df_filtrado))

    resumen = df_resumen_productos(df_filtrado)
    st.subheader("Resumen por producto")
    st.dataframe(resumen, use_container_width=True)

    st.subheader("Detalle de solicitudes")
    columnas = [
        "fecha", "mes", "rut", "nombre", "estado",
        "producto_1", "cantidad_1", "producto_2", "cantidad_2", "producto_3", "cantidad_3"
    ]
    columnas = [c for c in columnas if c in df_filtrado.columns]
    st.dataframe(df_filtrado[columnas], use_container_width=True)

    excel = crear_excel(df_filtrado[columnas])
    st.download_button(
        "Descargar Excel",
        data=excel,
        file_name=f"solicitudes_alimento_{mes_sel}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    st.caption("Para marcar entregado por ahora se puede editar el estado directamente en Supabase. En la siguiente versión agregamos botón desde este panel.")
