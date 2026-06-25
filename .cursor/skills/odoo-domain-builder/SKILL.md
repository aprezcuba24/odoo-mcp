---
name: odoo-domain-builder
description: >-
  Construye domains Odoo declarativos con OdooDomainBuilder en AdminMCP.
  Usar al añadir o modificar búsquedas Odoo, filtros base, criterios OR/AND,
  app/utils/odoo_domain.py o servicios search_* que usen search_read/search.
---

# OdooDomainBuilder

Patrón del proyecto para generar **domains Odoo** (`search_read`, `search`, etc.) sin ensamblar listas a mano.

Implementación: `app/utils/odoo_domain.py`  
Referencia de uso: `AndDomain` en `tests/test_odoo_domain.py`

> La búsqueda de clientes usa `res.partner.api_search_customers` y el catálogo de productos usa `product.product.api_search_products` / `api_get_product`; **no** requieren domain builder.

## Conceptos

| Pieza | Rol |
|-------|-----|
| `base_filters` | Filtros **siempre** aplicados (AND implícito al final) |
| `query` | Plantilla de criterios opcionales en **notación polaca** (`\|`, `&`) |
| kwargs del `__init__` | Valores por campo; clave = nombre del campo en la hoja del template |
| `build_domain()` | Devuelve la lista final para Odoo |

Reglas clave:

- Hoja del template: `[campo, OdooOperator.X]` — el operador va como enum, no como string.
- Si el kwargs de un campo es `None` o vacío (`""`), esa hoja **se omite**.
- Si ningún criterio de `query` aplica, solo se devuelve `base_filters`.
- El resultado concatena: `[criterios resueltos..., *base_filters]`.

Operadores disponibles (`OdooOperator`): `EQ` (`=`), `ILIKE` (`ilike`), `GT` (`>`).

## Ejemplo de referencia: AndDomain

```python
class AndDomain(OdooDomainBuilder):
    query = [
        "&",
        ["name", OdooOperator.EQ],
        ["email", OdooOperator.ILIKE],
    ]
```

Uso:

```python
AndDomain(name="Acme", email="a@b.com").build_domain()
# → ["&", ["name","=","Acme"], ["email","ilike","a@b.com"]]

AndDomain(name="Acme").build_domain()
# → [["name","=","Acme"]]   # email omitido, no queda AND huérfano
```

## Crear un nuevo builder

1. Subclase `OdooDomainBuilder` en el servicio correspondiente (`app/services/<recurso>.py`).
2. Define `base_filters` con condiciones invariantes del modelo.
3. Define `query` con hojas `[campo, operador]` y conectores `|` (OR) o `&` (AND).
4. Instancia con kwargs nombrados según los campos de las hojas.
5. Llama `build_domain()` y pásalo a `odoo.call(..., domain=domain)`.

### Plantilla AND (todos los criterios presentes)

```python
class AndDomain(OdooDomainBuilder):
    query = [
        "&",
        ["name", OdooOperator.EQ],
        ["email", OdooOperator.ILIKE],
    ]

AndDomain(name="Acme", email="a@b.com").build_domain()
# → ["&", ["name","=","Acme"], ["email","ilike","a@b.com"]]

AndDomain(name="Acme").build_domain()
# → [["name","=","Acme"]]   # email omitido, no queda AND huérfano
```

### Plantilla OR (cualquier criterio presente)

```python
query = [
    "|",
    ["name", OdooOperator.ILIKE],
    ["vat", OdooOperator.ILIKE],
]
```

Con un solo kwargs activo, el OR se simplifica a una sola condición (sin prefijo `|`).

## Notación polaca (Odoo)

```
"|", A, B     →  A OR B
"&", A, B     →  A AND B
"|", A, B, C  →  inválido en template (solo binario por nodo)
```

Para N condiciones OR/AND, `_combine_domains` aplana y repite el operador: `["|", c1, c2, c3]` cuando hay 3 hojas resueltas.

## Tests

Al cambiar un builder:

1. Añade casos en `tests/test_odoo_domain.py` (lógica del builder).
2. Si afecta un servicio, actualiza `tests/test_<servicio>_service.py` (domain enviado a `odoo.call`).

Patrón de aserción:

```python
assert MiDomain(name="x").build_domain() == [
    ["name", "ilike", "x"],
    *MiDomain.base_filters,
]
```

## Errores frecuentes

- **String en lugar de enum**: `["name", "ilike"]` → usar `OdooOperator.ILIKE`.
- **Valor en la hoja del template**: `[campo, op, valor]` en `query` — los valores van solo en kwargs.
- **Campo kwargs distinto al template**: la clave debe coincidir exactamente con el primer elemento de la hoja.
- **Olvidar `base_filters`**: van al final del domain; en Odoo actúan como AND con lo anterior.
