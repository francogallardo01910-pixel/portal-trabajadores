# ALFA Control Portal v1.0

Portal externo para solicitud mensual de alimento de trabajadores.

## Funciones

- Ingreso por RUT.
- Solicitud de hasta 3 alimentos.
- Máximo 3 sacos por alimento.
- Bloqueo automático día 11 en adelante.
- Modo prueba activable desde Secrets.
- Panel administrador.
- Exportación a Excel.
- Conexión con Supabase usando REST API.

## Secrets requeridos en Streamlit

```toml
SUPABASE_URL = "https://TU_PROYECTO.supabase.co"
SUPABASE_KEY = "TU_ANON_KEY_LEGACY_QUE_EMPIEZA_CON_eyJ"
ADMIN_PASSWORD = "1234"
MODO_PRUEBA = "SI"
```

Cuando termine la prueba, cambiar:

```toml
MODO_PRUEBA = "NO"
```
