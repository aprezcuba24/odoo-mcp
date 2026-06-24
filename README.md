# admin-mcp

Servidor [MCP](https://modelcontextprotocol.io/) (Model Context Protocol) en Python para operaciones de administración Odoo. Scaffold arquitectónico basado en [ApkMCP](../ApkMCP), con **FastMCP** y transporte **Streamable HTTP**.

Incluye búsqueda de clientes conectada: **service → resource → tool**.

## Requisitos

- Python 3.11+
- Para desarrollo con [MCP Inspector](https://modelcontextprotocol.io/docs/tools/inspector): Node.js **22.7.5+** y **pnpm**

## Instalación

```bash
cd AdminMCP
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[lambda]"
```

Con [uv](https://docs.astral.sh/uv/):

```bash
uv sync --all-extras
```

## Configuración

Copia `.env.example` a `.env`:

| Variable | Descripción | Default |
|----------|-------------|---------|
| `ADMIN_API_TIMEOUT` | Timeout HTTP en segundos | `30` |
| `MCP_HOST` / `MCP_PORT` / `MCP_PATH` | Bind y ruta MCP | `0.0.0.0:8001/mcp` |

### Autenticación (`auth-key`)

Cada petición HTTP al endpoint MCP debe incluir la cabecera **`auth-key`**: `Bearer` + `base64(BASE_URL|API_KEY[|database])`.

- `BASE_URL`: URL HTTPS del servidor Odoo (sin barra final), p. ej. `https://mi-empresa.onrender.com`
- `API_KEY`: clave API de un usuario bot de Odoo (scope rpc)
- `database` (opcional): nombre de la base de datos cuando el servidor tiene varias (`X-Odoo-Database`)

Generar el valor en local:

```bash
# Sin base de datos explícita
pnpm auth-key -- https://mi-empresa.onrender.com|99031c76-d288-41ea-866b-ef656f58e497

# Con base de datos (multi-DB)
pnpm auth-key -- https://mi-empresa.onrender.com|99031c76-d288-41ea-866b-ef656f58e497|mi_db
```

El servidor decodifica URL, API key y database opcional, y prepara el cliente httpx para llamadas JSON-2 a Odoo (`POST /json/2/{modelo}/{metodo}`).

## Ejecución

```bash
python -m app
# o
admin-mcp
```

Desarrollo con Inspector:

```bash
pnpm install
pnpm dev
```

Inspector usa `dev/mcp-inspector.config.json` (puerto **8001**, distinto de ApkMCP en 8000). Configura el header `auth-key` en el Inspector antes de invocar tools/resources.

## Superficie MCP

| Tipo | Nombre | URI / descripción |
|------|--------|-------------------|
| Resource | Listado de clientes | `app://customers` |
| Resource | Búsqueda de clientes | `app://customers{?name,vat,email,limit}` |
| Tool (lectura) | `read_customers` | Espejo de los resources (ChatGPT) |
| Prompt | `admin_assistant` | Flujo guiado de listado y búsqueda |

## Arquitectura

```
app/
├── server/          # FastMCP, lifespan, middleware auth-key, DI, instructions
├── clients/         # OdooJson2Client (JSON-2 API oficial)
├── services/        # Lógica reutilizable (sin decoradores MCP)
├── resources/       # @mcp.resource  app://...
├── tools/           # @mcp.tool acciones
│   └── tool_resources/  # read_* espejo de resources
├── prompts/         # @mcp.prompt
├── utils/           # app_key_codec, excepciones
└── cli/             # admin-mcp-auth-key
```

Registro por imports con efecto lateral en `app/server/__init__.py`.

Flujo de búsqueda de clientes:

1. `AppKeyMiddleware` decodifica `auth-key` → `AppContext`
2. Resource `app://customers` o tool `read_customers` → `services/customers.py`

### Cómo extender

1. Añadir función en `app/services/<dominio>.py`
2. Exponer `@mcp.resource` en `app/resources/<dominio>.py`
3. Espejo `read_*` en `app/tools/tool_resources/<dominio>.py`
4. Tools de acción en `app/tools/<dominio>.py`
5. Registrar módulos en los `__init__.py` correspondientes
6. Actualizar `app/server/instructions.py`

## Configuración Cursor MCP

```json
{
  "mcpServers": {
    "admin-mcp": {
      "url": "http://127.0.0.1:8001/mcp",
      "headers": {
        "auth-key": "Bearer <base64(BASE_URL|API_KEY[|database])>"
      }
    }
  }
}
```

## Tests

```bash
pnpm test
# o
pytest
```

## Despliegue (AWS Lambda)

```bash
pnpm deploy
```

Requiere credenciales AWS y `SERVERLESS_ACCESS_KEY`. El workflow `.github/workflows/main.yml` despliega en push a `main`.

## Relación con ApkMCP

AdminMCP replica la arquitectura de ApkMCP (capas, auth-key, Lambda, Inspector) sin la lógica de tienda (catálogo, carrito, order_bridge, OpenAPI generado, DynamoDB).
