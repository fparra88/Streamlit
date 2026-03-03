Eres un Asistente FrontEnd muy experimentado, experto en Streamlit, pandas y requests

Introducción
Este repositorio/guía está pensado para construir módulos-agente que administren las responsabilidades de negocio en un WRP: inventario, cotizaciones, traspasos y ventas.
Usamos Streamlit para UI ligera, pandas para manipulación tabular y requests para llamadas HTTP a APIs externas (ERP, proveedores, pasarelas).
Prioridad: claridad, manejo robusto de errores y consistencia en nombres y comentarios.
Arquitectura sugerida
Frontend: Streamlit (pantallas por módulo).
Lógica/servicios: módulos Python separados por responsabilidad (api_clients, services, validators).
Datos temporales/transformaciones: pandas DataFrames dentro de servicios.
Persistencia: APIs externas o base de datos (no entraremos en DB específica aquí).
Logging: archivo de logs + consola.
Diagrama lógico (conceptual):

streamlit_app.py -> controllers -> services -> api_clients -> (APIs externas) -> utils (validators, transforms) -> models (DTOs simples si aplica)
Convenciones de nombres
Idioma del código: inglés para variables y funciones (mejor compatibilidad), pero comentarios y documentación en español (LatAm).
Estilo de funciones y variables:
Funciones: snake_case (ej.: get_item_stock, calculate_quote)
Variables locales: snake_case con máximo dos palabras separadas por un solo "_" (ej.: item_id, unit_price, qty) — no más de dos palabras.
Clases: PascalCase (ej.: InventoryService, ApiClient)
Constantes: UPPER_SNAKE (ej.: API_TIMEOUT)
Uso de camelCase: solo para JSON externos o cuando la API lo requiera. Internamente convertir a snake_case y documentar la conversión.
Comentarios:
Comentarios "como si fuese el programador": explico por qué hago pasos concretos (no decir obviedades).
Evitar comentarios redundantes que repitan lo que hace el código; explicar intención, supuestos, y límites.
Ejemplos de nombres permitidos:

item_id (válido)
unit_price (válido)
qty (válido)
inventory_count (NO: tres palabras — cambiar a inventory_qty o stock_qty)
Estructura de archivos y carpetas (sugerida)
app/
streamlit_app.py
pages/
inventario.py
cotizaciones.py
traspasos.py
ventas.py
controllers/
inventory_controller.py
quote_controller.py
services/
inventory_service.py
quote_service.py
transfer_service.py
api_clients/
api_client.py
supplier_client.py
utils/
validators.py
transforms.py
errors.py
models/
dto.py
conf/
settings.py
logs/
app.log
tests/
test_inventory.py
test_quotes.py
README.md
AGENTES.MD
Guía de desarrollo: componentes principales
5.1 Conexión a APIs (requests)

Reglas:
Definir API_TIMEOUT constante.
Usar sesiones de requests.Session() para reuso de conexiones y performance.
Implementar reintentos simples con backoff exponencial (máx 3 intentos).
Normalizar respuestas: validar status_code y esquema esperado; convertir claves camelCase -> snake_case al ingresar al sistema.
Patrón de api_client.py (resumido):

create_session() -> retorna Session con headers base
safe_request(method, url, params=None, json=None) -> maneja timeouts, reintentos, errores HTTP y parseo JSON
map_response_keys(response_json) -> convierte camelCase a snake_case (si aplica)
Errores a definir en utils/errors.py:

ApiError(Exception) — incluye status, message, payload
ValidationError(Exception)
ExternalServiceError(Exception)
5.2 Manejo de DataFrames con pandas

Reglas prácticas:
Columnas internas: nombres en snake_case, máximo dos palabras por columna.
Evitar nombres con espacios o caracteres especiales.
Convertir tipos explícitamente: fechas con pd.to_datetime, numéricos con pd.to_numeric.
Evitar operaciones in-place que sean ambiguas; preferir asignación clara: df = df.drop(columns=[...]).
Documentar suposiciones (por ejemplo: "qty es entero no negativo", "unit_price es float con 2 decimales").
Funciones útiles en transforms.py:

normalize_columns(df, mapping) -> renombrar columnas
ensure_types(df, schema) -> convierte tipos y levanta ValidationError si falla
safe_merge(df_left, df_right, on, how='left', suffixes=('_L','_R')) -> validaciones post-merge
5.3 Interfaz con Streamlit

Reglas:
Cada página en pages/ corresponde a un módulo (inventario, cotizaciones, traspasos, ventas).
Mantener la UI ligera: inputs, tablas con st.dataframe, botones con confirmación.
Evitar lógica pesada en la UI: invocar controllers/services.
Manejar estado con st.session_state usando claves cortas en snake_case (ej.: selected_item).
Mensajes de usuario en español claro y amigable.
Mostrar errores capturados de manera legible (no stack trace en producción).
Patrón de controller:

controller recibe inputs de Streamlit, valida con validators.py, llama al service y retorna resultados o errores amigables.
Los servicios retornan objetos o DataFrames bien formados.
5.4 Operaciones clave

Inventario:

Funciones:
get_item_stock(item_id) -> retorna stock disponible y su ubicación
list_inventory(filters) -> DataFrame con columnas: item_id, name, stock_qty, unit_price
adjust_inventory(item_id, qty_delta, reason) -> registra movimiento y actualiza stock (use transacción o llamada API)
Validaciones:
qty must be integer y no negativo si es operación directa; en ajuste usar qty_delta que puede ser negativo.
Cotizaciones:

Funciones:
create_quote(customer_id, items_df, expires_at) -> genera cotización con totales, impuestos y descuentos
calculate_quote_totals(items_df, discounts=None, taxes=None) -> retorna DataFrame con subtotales y total_final
Reglas:
Mantener copy de items como DataFrame con columnas cortas: item_id, qty, unit_price, discount_pct
Validar que qty > 0 y que stock disponible cubre la cotización opcionalmente.
Traspasos:

Funciones:
create_transfer(from_loc, to_loc, items_df) -> valida stock en origen y reserva en destino
complete_transfer(transfer_id) -> aplica movimientos finales
Reglas:
Reservas deben marcar estado: PENDING -> IN_TRANSIT -> COMPLETED
Manejar idempotencia en endpoints externos (usar transfer_reference)
Ventas:

Funciones:
create_sale(customer_id, items_df, payment_info) -> verifica stock, genera movimiento y confirma pago
return_sale(sale_id, items_df, reason) -> actualiza inventario y registra nota de crédito
Manejo de errores y logging
Principios:
Atrapar errores esperados y transformar en mensajes de usuario claros.
No exponer trazas internas en la UI (solo en logs).
Usar logging estructurado; incluir contextos: user_id, operation, reference_id.
Cada servicio debe documentar los tipos de errores que puede lanzar (ApiError, ValidationError, ExternalServiceError).
Ejemplo de patrón:

try:
  resultado = service.do_something()
except ValidationError as e:
  logger.warning("validación fallida", extra={...})
  mostrar_error_usuario("Datos inválidos: " + str(e))
except ApiError as e:
  logger.error("API falló", extra={...})
  mostrar_error_usuario("No se pudo conectar con el servicio externo, intente más tarde.")
except Exception as e:
  logger.exception("Error inesperado")
  mostrar_error_usuario("Ocurrió un error interno. Contacte a soporte.")

Implementar decorador @handle_errors(controller_func) que capture y transforme excepciones en respuestas uniformes.

Testing básico y validaciones
Tests unitarios para:
Transforms: conversión de columnas y tipos.
Services: cálculos de totales, descuentos, validaciones de stock.
API client: mockear requests y validar reintentos y parseo de JSON.
Casos importantes:
Cotización con descuento máximo, sin stock, precios nulos.
Traspaso parcial (stock insuficiente).
Creación de venta concurrente (simular race condition simple).
Recomendación: usar pytest y requests-mock.