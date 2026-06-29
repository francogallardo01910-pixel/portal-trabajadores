from datetime import datetime
from io import BytesIO
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="ALFA Control Portal",
    page_icon="📦",
    layout="centered",
)

# =============================
# CONFIGURACIÓN
# =============================
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "").strip().rstrip("/").replace("/rest/v1", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "").strip()
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "1234")
MODO_PRUEBA = st.secrets.get("MODO_PRUEBA", "SI").upper() == "SI"

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("Faltan SUPABASE_URL o SUPABASE_KEY en los Secrets de Streamlit.")
    st.stop()

REST_URL = f"{SUPABASE_URL}/rest/v1"
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}

# =============================
# ESTILO
# =============================
st.markdown(
    """
    <style>
    .main { background-color:#f7faf8; }
    .block-container { max-width: 820px; padding-top: 1.2rem; }
    .titulo { text-align:center; color:#0B6B3A; font-size:34px; font-weight:800; }
    .subtitulo { text-align:center; color:#475569; font-size:17px; margin-bottom:24px; }
    .card { background:white; padding:22px; border-radius:18px; box-shadow:0 2px 14px rgba(0,0,0,.08); margin-bottom:18px; }
    .ok { color:#166534; font-weight:700; }
    .warn { color:#b45309; font-weight:700; }
    </style>
    """,
    unsafe_allow_html=True,
)

# =============================
# FUNCIONES SUPABASE REST
# =============================
def supabase_get(tabla: str, params: dict | None = None):
    r = requests.get(f"{REST_URL}/{tabla}", headers=HEADERS, params=params or {}, timeout=25)
    if r.status_code >= 400:
        raise RuntimeError(f"Error GET {tabla}: {r.text}")
    return r.json()


def supabase_post(tabla: str, data: dict):
    r = requests.post(f"{REST_URL}/{tabla}", headers=HEADERS, json=data, timeout=25)
    if r.status_code >= 400:
        raise RuntimeError(f"Error POST {tabla}: {r.text}")
    return r.json()


def supabase_patch(tabla: str, params: dict, data: dict):
    r = requests.patch(f"{REST_URL}/{tabla}", headers=HEADERS, params=params, json=data, timeout=25)
    if r.status_code >= 400:
        raise RuntimeError(f"Error PATCH {tabla}: {r.text}")
    return r.json()


def mes_actual() -> str:
    return datetime.now().strftime("%Y-%m")


def solicitudes_abiertas() -> bool:
    if MODO_PRUEBA:
        return True
    return datetime.now().day <= 10


def obtener_trabajador(rut: str):
    rut = rut.strip()
    data = supabase_get(
        "trabajadores",
        {
            "select": "rut,nombre,activo",
            "rut": f"eq.{rut}",
            "activo": "eq.true",
            "limit": "1",
        },
    )
    return data[0] if data else None


def obtener_productos():
    data = supabase_get(
        "productos_alimento",
        {
            "select": "producto,formato,activo",
            "activo": "eq.true",
            "order": "producto.asc",
        },
    )
    productos = []
    for p in data:
        producto = (p.get("producto") or "").strip()
        formato = (p.get("formato") or "").strip()
        nombre = f"{producto} {formato}".strip()
        if nombre:
            productos.append(nombre)
    return productos


def solicitud_existente(rut: str, mes: str):
    data = supabase_get(
        "solicitudes_alimento",
        {
            "select": "*",
            "rut": f"eq.{rut}",
            "mes": f"eq.{mes}",
            "limit": "1",
        },
    )
    return data[0] if data else None


def obtener_solicitudes(mes: str | None = None):
    params = {"select": "*", "order": "fecha.desc"}
    if mes:
        params["mes"] = f"eq.{mes}"
    return supabase_get("solicitudes_alimento", params)


def limpiar_rut(rut: str) -> str:
    return rut.strip().replace(".", "").upper()


def df_solicitudes(data):
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    columnas = [
        "id", "fecha", "mes", "rut", "nombre", "producto_1", "cantidad_1",
        "producto_2", "cantidad_2", "producto_3", "cantidad_3", "estado"
    ]
    for col in columnas:
        if col not in df.columns:
            df[col] = ""
    return df[columnas]


def excel_bytes(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Solicitudes")
        if not df.empty:
            resumen = []
            for _, row in df.iterrows():
                for n in [1, 2, 3]:
                    prod = row.get(f"producto_{n}")
                    cant = row.get(f"cantidad_{n}")
                    if pd.notna(prod) and str(prod).strip() and pd.notna(cant):
                        resumen.append({"Producto": prod, "Cantidad": int(cant)})
            if resumen:
                pd.DataFrame(resumen).groupby("Producto", as_index=False)["Cantidad"].sum().to_excel(
                    writer, index=False, sheet_name="Resumen por producto"
                )
    return output.getvalue()

# =============================
# ENCABEZADO
# =============================
st.markdown('<div class="titulo">ALFA Control Portal</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitulo">Solicitud mensual de alimento para trabajadores</div>', unsafe_allow_html=True)

menu = st.sidebar.radio("Menú", ["Trabajador", "Administrador"])

st.info("Las solicitudes se reciben del día 1 al día 10. El retiro será el día 15.")
if MODO_PRUEBA:
    st.warning("Modo prueba activo: el portal está abierto aunque no sea día 1 al 10.")

# =============================
# PORTAL TRABAJADOR
# =============================
if menu == "Trabajador":
    if not solicitudes_abiertas():
        st.warning("Las solicitudes de este mes ya fueron cerradas. Consulte nuevamente el próximo mes.")
        st.stop()

    rut = limpiar_rut(st.text_input("Ingrese su RUT", placeholder="Ej: 12345678-9"))

    if rut:
        try:
            trabajador = obtener_trabajador(rut)
        except Exception as e:
            st.error("No se pudo conectar con la base de datos. Revise la configuración de Supabase.")
            st.exception(e)
            st.stop()

        if not trabajador:
            st.error("RUT no encontrado o trabajador inactivo.")
            st.stop()

        nombre = trabajador["nombre"]
        st.success(f"Bienvenido/a {nombre}")

        mes = mes_actual()
        existente = solicitud_existente(rut, mes)
        if existente:
            st.warning("Usted ya realizó su solicitud este mes.")
            st.write("Estado:", existente.get("estado", "Pendiente"))
            st.stop()

        productos = obtener_productos()
        if not productos:
            st.error("No hay productos activos cargados en Supabase.")
            st.stop()

        st.markdown("### 📦 Seleccione hasta 3 alimentos")
        st.caption("Cada alimento permite máximo 3 sacos. Pueden ser iguales o diferentes.")

        solicitudes = []
        for i in range(1, 4):
            with st.expander(f"Alimento {i}", expanded=(i == 1)):
                usar = True if i == 1 else st.checkbox(f"Agregar alimento {i}", key=f"usar_{i}")
                if usar:
                    producto = st.selectbox(f"Producto {i}", productos, key=f"producto_{i}")
                    cantidad = st.number_input(f"Cantidad {i}", min_value=1, max_value=3, step=1, key=f"cantidad_{i}")
                    solicitudes.append((producto, int(cantidad)))

        if st.button("Enviar solicitud", type="primary"):
            data = {
                "mes": mes,
                "rut": rut,
                "nombre": nombre,
                "producto_1": solicitudes[0][0] if len(solicitudes) >= 1 else None,
                "cantidad_1": solicitudes[0][1] if len(solicitudes) >= 1 else None,
                "producto_2": solicitudes[1][0] if len(solicitudes) >= 2 else None,
                "cantidad_2": solicitudes[1][1] if len(solicitudes) >= 2 else None,
                "producto_3": solicitudes[2][0] if len(solicitudes) >= 3 else None,
                "cantidad_3": solicitudes[2][1] if len(solicitudes) >= 3 else None,
                "estado": "Pendiente",
            }
            try:
                supabase_post("solicitudes_alimento", data)
                st.success("Solicitud enviada correctamente. Retiro programado para el día 15.")
                st.balloons()
            except Exception as e:
                st.error("No se pudo guardar la solicitud.")
                st.exception(e)

# =============================
# PANEL ADMINISTRADOR
# =============================
if menu == "Administrador":
    clave = st.text_input("Clave administrador", type="password")
    if clave != ADMIN_PASSWORD:
        st.info("Ingrese la clave para acceder al panel administrador.")
        st.stop()

    st.markdown("### 📊 Panel administrador")
    mes = st.text_input("Mes a revisar", value=mes_actual(), help="Formato YYYY-MM")

    try:
        data = obtener_solicitudes(mes)
    except Exception as e:
        st.error("No se pudieron cargar las solicitudes.")
        st.exception(e)
        st.stop()

    df = df_solicitudes(data)
    st.write(f"Solicitudes encontradas: {len(df)}")
    st.dataframe(df, use_container_width=True)

    if not df.empty:
        filas_resumen = []
        for _, row in df.iterrows():
            for n in [1, 2, 3]:
                prod = row.get(f"producto_{n}")
                cant = row.get(f"cantidad_{n}")
                if pd.notna(prod) and str(prod).strip() and pd.notna(cant):
                    filas_resumen.append({"Producto": prod, "Cantidad": int(cant)})
        if filas_resumen:
            resumen = pd.DataFrame(filas_resumen).groupby("Producto", as_index=False)["Cantidad"].sum()
            st.markdown("### Resumen por producto")
            st.dataframe(resumen, use_container_width=True)

        st.download_button(
            "📥 Descargar Excel",
            data=excel_bytes(df),
            file_name=f"solicitudes_alimento_{mes}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        st.markdown("### Marcar como entregado")
        ids = df["id"].astype(str).tolist()
        id_sel = st.selectbox("Seleccione ID", ids)
        if st.button("Marcar entregado"):
            supabase_patch("solicitudes_alimento", {"id": f"eq.{id_sel}"}, {"estado": "Entregado"})
            st.success("Solicitud marcada como entregada. Actualice la página para ver el cambio.")
