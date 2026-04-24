import streamlit as st
import requests
import pandas as pd
import math
import time

API_BASE_URL = st.session_state.ip

toks = {
    "Authorization": f"Bearer {st.session_state.token}"
}

USOS_CFDI = [
    "G01 - Adquisición de mercancías",
    "G02 - Devoluciones, descuentos o bonificaciones",
    "G03 - Gastos en general",
    "I01 - Construcciones",
    "I02 - Mobiliario y equipo de oficina por inversiones",
    "I03 - Equipo de transporte",
    "I04 - Equipo de cómputo y accesorios",
    "I05 - Dados, troqueles, moldes, matrices y herramental",
    "I06 - Comunicaciones telefónicas",
    "I07 - Comunicaciones satelitales",
    "I08 - Otra maquinaria y equipo",
    "D01 - Honorarios médicos, dentales y gastos hospitalarios",
    "D02 - Gastos médicos por incapacidad o discapacidad",
    "D03 - Gastos funerales",
    "D04 - Donativos",
    "D05 - Intereses reales efectivamente pagados por créditos hipotecarios (casa habitación)",
    "D06 - Aportaciones voluntarias al SAR",
    "D07 - Primas por seguros de gastos médicos",
    "D08 - Gastos de transportación escolar obligatoria",
    "D09 - Depósitos en cuentas especiales para el ahorro, planes de pensiones",
    "D10 - Pagos por servicios educativos (colegiaturas)",
    "S01 - Sin efectos fiscales",
    "CP01 - Pagos",
    "CN01 - Nómina",
]

REGIMENES = [
    "601 - General de Ley Personas Morales",
    "603 - Personas Morales con Fines no Lucrativos",
    "605 - Sueldos y Salarios e Ingresos Asimilados a Salarios",
    "606 - Arrendamiento",
    "607 - Régimen de Enajenación de acciones en bolsa de valores",
    "608 - Enajenación de bienes",
    "609 - Consolidación",
    "610 - Residentes en el Extranjero sin Establecimiento Permanente en México",
    "611 - Ingresos por Dividendos (socios y accionistas)",
    "612 - Personas Físicas con Actividades Empresariales y Profesionales",
    "614 - Intereses",
    "615 - De los demás ingresos",
    "616 - Sin obligaciones fiscales",
    "620 - Sociedades Cooperativas de Producción que optan por diferir sus ingresos",
    "621 - Incorporación Fiscal",
    "622 - Actividades Agrícolas, Ganaderas, Silvícolas y Pesqueras",
    "623 - Opcional para Grupos de Sociedades",
    "624 - Coordinados",
    "625 - Régimen de las Actividades Empresariales con ingresos a través de Plataformas Tecnológicas",
    "626 - Régimen Simplificado de Confianza",
]


def sanitize_row_data(row):
    campos_string = ['contacto', 'telefono', 'empresa', 'direccion', 'email', 'nombre', 'rfc', 'usuario']
    campos_bool = ['credito']
    campos_numerico = ['id']

    sanitized = {}
    for key, value in row.items():
        try:
            if isinstance(value, float) and math.isnan(value):
                if key in campos_string:
                    sanitized[key] = ""
                elif key in campos_bool:
                    sanitized[key] = False
                elif key in campos_numerico:
                    continue
                else:
                    sanitized[key] = ""
            elif value is None:
                if key in campos_string:
                    sanitized[key] = ""
                elif key in campos_bool:
                    sanitized[key] = False
                elif key in campos_numerico:
                    continue
                else:
                    sanitized[key] = ""
            elif isinstance(value, str) and value.strip() == "":
                sanitized[key] = "" if key not in campos_bool else False
            else:
                if key in campos_bool and not isinstance(value, bool):
                    sanitized[key] = bool(value) if value else False
                else:
                    sanitized[key] = value
        except Exception:
            sanitized[key] = "" if key in campos_string else (False if key in campos_bool else value)

    return sanitized


def _init_state():
    if "clientes_data" not in st.session_state:
        st.session_state.clientes_data = None
    if "cliente_edit" not in st.session_state:
        st.session_state.cliente_edit = None


def _cargar_clientes():
    try:
        with st.spinner("Cargando clientes..."):
            response = requests.get(f"{API_BASE_URL}/zeutica/clientes", headers=toks)
        if response.status_code == 200:
            st.session_state.clientes_data = pd.json_normalize(response.json())
        else:
            st.error(f"Error al obtener clientes: {response.status_code}")
    except Exception as e:
        st.error(f"Falla de conexión: {e}")


def _v(cliente, key, default=""):
    """Extrae un valor del dict del cliente en edición, manejando None y NaN."""
    if not cliente:
        return default
    val = cliente.get(key, default)
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return default
    return val


def _idx(lista, val):
    """Devuelve el índice de `val` en `lista`. Primero exacto, luego por código (3 chars)."""
    if not val:
        return 0
    if val in lista:
        return lista.index(val)
    prefix = str(val)[:3]
    for i, opt in enumerate(lista):
        if opt.startswith(prefix):
            return i
    return 0


def app():
    _init_state()

    cliente_edit = st.session_state.cliente_edit
    modo = "edicion" if cliente_edit else "alta"

    # --- ENCABEZADO ---
    col_t, col_badge = st.columns([4, 1])
    with col_t:
        st.title("📂 Alta / Edición de Clientes")
    with col_badge:
        if modo == "edicion":
            st.markdown(
                "<div style='background:#1e6f3e;color:white;padding:6px 12px;"
                "border-radius:8px;text-align:center;margin-top:16px;font-size:13px;'>"
                "✏️ Modo edición</div>",
                unsafe_allow_html=True,
            )

    # --- EXPANDER: BUSCAR CLIENTE ---
    with st.expander("🔍 Buscar cliente existente para editar", expanded=False):
        col_btn, col_info = st.columns([1, 3])
        with col_btn:
            if st.button("🔄 Cargar / Actualizar", key="btn_cargar_clientes"):
                _cargar_clientes()

        if st.session_state.clientes_data is not None:
            df = st.session_state.clientes_data

            buscar = st.text_input(
                "Filtrar por nombre o RFC:",
                key="buscar_cliente",
                placeholder="Escribe para filtrar...",
            )

            if buscar:
                mask = df["nombre"].str.contains(buscar, case=False, na=False) | df[
                    "rfc"
                ].str.contains(buscar, case=False, na=False)
                df_filtrado = df[mask].reset_index(drop=True)
            else:
                df_filtrado = df.reset_index(drop=True)

            if df_filtrado.empty:
                st.warning("No se encontraron clientes con ese criterio.")
            else:
                cols_visibles = [c for c in ["id", "nombre", "rfc", "email", "telefono", "empresa"] if c in df_filtrado.columns]
                st.dataframe(
                    df_filtrado[cols_visibles].head(30),
                    use_container_width=True,
                    hide_index=True,
                )

                opciones_idx = df_filtrado.index.tolist()
                labels = df_filtrado.apply(
                    lambda r: f"[{r.get('id', '?')}] {r.get('nombre', '')} — {r.get('rfc', '')}",
                    axis=1,
                ).tolist()

                sel = st.selectbox(
                    "Selecciona un cliente:",
                    options=opciones_idx,
                    format_func=lambda i: labels[i],
                    key="sel_cliente",
                )

                if st.button("✏️ Cargar en formulario", type="primary", key="btn_cargar_form"):
                    st.session_state.cliente_edit = df_filtrado.loc[sel].to_dict()
                    st.rerun()

    st.divider()

    # --- CABECERA DEL FORMULARIO ---
    if modo == "edicion":
        col_h, col_cancel = st.columns([3, 1])
        with col_h:
            st.subheader(f"✏️ Editando: **{_v(cliente_edit, 'nombre')}**")
        with col_cancel:
            if st.button("➕ Nuevo cliente", type="secondary", key="btn_modo_alta"):
                st.session_state.cliente_edit = None
                st.rerun()
    else:
        st.subheader("➕ Nuevo Cliente")
        st.markdown("Ingresa los datos del cliente para registrarlo en la base de datos de AWS.")

    # Toggle crédito fuera del form — key dinámica para reflejar el cliente seleccionado
    credito_key = f"toggle_credito_{_v(cliente_edit, 'id', 'nuevo')}"
    credito_val = bool(_v(cliente_edit, "credito", False))
    credito_cliente = st.toggle("¿El cliente cuenta con crédito?", value=credito_val, key=credito_key)

    # Key dinámica del form → fuerza re-render al cambiar de cliente o de modo
    form_key = f"form_cliente_{_v(cliente_edit, 'id', 'nuevo')}"

    with st.form(form_key, clear_on_submit=(modo == "alta")):
        col1, col2 = st.columns(2)

        with col1:
            nombre = st.text_input("Nombre Completo *", value=_v(cliente_edit, "nombre"))
            rfc = st.text_input("RFC *", value=_v(cliente_edit, "rfc"))
            telefono = st.text_input("Teléfono", value=_v(cliente_edit, "telefono"))
            cp = st.text_input("Código Postal *", value=_v(cliente_edit, "cp"))
            usocfdi = st.selectbox(
                "Uso de CFDI",
                USOS_CFDI,
                index=_idx(USOS_CFDI, _v(cliente_edit, "usocfdi")),
            )
            frecuencia = st.text_input(
                "Frecuencia de compra",
                value=_v(cliente_edit, "frecuencia", "Mensual"),
            )

        with col2:
            email = st.text_input("Correo Electrónico *", value=_v(cliente_edit, "email"))
            direccion = st.text_area(
                "Dirección Física (Opcional)",
                value=_v(cliente_edit, "direccion"),
                height=100,
            )
            empresa = st.text_input("Empresa (opcional)", value=_v(cliente_edit, "empresa"))
            regimen = st.selectbox(
                "Régimen Fiscal",
                REGIMENES,
                index=_idx(REGIMENES, _v(cliente_edit, "regimen")),
            )
            contacto = st.text_input("Datos de contacto", value=_v(cliente_edit, "contacto"))

            monto_credito = None
            if credito_cliente:
                monto_raw = _v(cliente_edit, "monto_credito", 500)
                try:
                    monto_default = int(float(monto_raw))
                except (ValueError, TypeError):
                    monto_default = 500
                monto_credito = st.number_input(
                    "Monto del crédito",
                    min_value=500,
                    step=1,
                    value=max(500, monto_default),
                )

        btn_label = "💾 Guardar Cambios" if modo == "edicion" else "💾 Registrar Cliente"
        submitted = st.form_submit_button(btn_label, type="primary", use_container_width=True)

        if submitted:
            if not nombre or not rfc:
                st.warning("⚠️ Nombre y RFC son campos obligatorios.")
            else:
                payload = {
                    "nombre": nombre.strip(),
                    "email": email.strip() if email else "",
                    "empresa": empresa.strip() if empresa else "",
                    "contacto": contacto.strip() if contacto else "",
                    "telefono": telefono.strip() if telefono else "",
                    "direccion": direccion.strip() if direccion else "",
                    "rfc": rfc.strip(),
                    "cp": cp.strip() if cp else "",
                    "regimen": regimen.strip() if regimen else "",
                    "usocfdi": usocfdi.strip() if usocfdi else "",
                    "frecuencia": frecuencia.strip() if frecuencia else "",
                    "credito": bool(credito_cliente),
                    "usuario": st.session_state.usuario_nombre.strip()
                    if st.session_state.usuario_nombre
                    else "",
                }
                if credito_cliente and monto_credito is not None:
                    payload["monto_credito"] = int(monto_credito)
                if modo == "edicion":
                    cliente_id = cliente_edit.get("id")
                    if isinstance(cliente_id, float):
                        cliente_id = int(cliente_id)
                    payload["id"] = cliente_id
                    endpoint = f"{API_BASE_URL}/zeutica/editcliente"
                else:
                    endpoint = f"{API_BASE_URL}/zeutica/clientenuevo"
                st.session_state.cliente_pendiente = {
                    "payload": payload,
                    "endpoint": endpoint,
                    "modo": modo,
                    "nombre": nombre.strip(),
                }

    if st.session_state.get("cliente_pendiente"):
        cp_data = st.session_state.cliente_pendiente
        accion = "actualizar" if cp_data["modo"] == "edicion" else "registrar"
        st.warning(
            f"⚠️ ¿Confirmas {accion} al cliente **{cp_data['nombre']}**?"
        )
        col_ok, col_cancel = st.columns(2)
        with col_ok:
            if st.button("✅ Sí, confirmar", type="primary", use_container_width=True):
                try:
                    with st.spinner("Guardando..."):
                        res = requests.post(cp_data["endpoint"], headers=toks, json=cp_data["payload"])
                    st.session_state.cliente_pendiente = None
                    if res.status_code == 200:
                        st.balloons()
                        if cp_data["modo"] == "edicion":
                            st.success("✅ Cliente actualizado correctamente.")
                            st.session_state.cliente_edit = None
                            st.session_state.clientes_data = None
                            time.sleep(1)
                            st.rerun()
                        else:
                            data_resp = res.json()
                            st.success(f"✅ ¡Cliente registrado! ID asignado: {data_resp.get('id')}")
                    else:
                        st.error(f"❌ Error {res.status_code}: {res.text}")
                except requests.exceptions.ConnectionError:
                    st.error("🔌 No se pudo conectar con la API. Verifica que el servidor esté activo.")
                    st.session_state.cliente_pendiente = None
                except Exception as e:
                    st.error(f"Ocurrió un error inesperado: {e}")
                    st.session_state.cliente_pendiente = None
        with col_cancel:
            if st.button("❌ Cancelar", use_container_width=True):
                st.session_state.cliente_pendiente = None
                st.rerun()


if __name__ == "__main__":
    app()
