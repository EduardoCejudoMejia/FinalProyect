# Arquitectura

```mermaid
flowchart LR
  Client[Cliente] --> API[FastAPI / adaptador HTTP]
  API --> UseCases[OrderService / casos de uso]
  UseCases --> Ports[Puertos: repositorio y eventos]
  Ports --> SQL[SQLAlchemy + SQLite/PostgreSQL]
  Ports --> Logs[Eventos estructurados]
```

Las dependencias apuntan hacia dentro: `domain` no importa infraestructura; `application` sólo conoce protocolos. Los adaptadores se inyectan desde `api.py`.

## Secuencia de creación

```mermaid
sequenceDiagram
  participant C as Cliente
  participant A as API
  participant U as Caso de uso
  participant R as Repositorio
  C->>A: POST /orders + Bearer
  A->>U: create_order
  U->>R: add(Order)
  R-->>U: Order
  U-->>A: Order
  A-->>C: 201 JSON
```
