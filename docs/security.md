# Seguridad y auditoría

- Endpoints de pedidos protegidos con JWT Bearer HS256; el secreto se recibe por entorno.
- Validación de datos por Pydantic (correo, rangos, límites de colecciones) y reglas adicionales en el dominio.
- No se versionan secretos: usar `.env` local a partir de `.env.example` y un gestor de secretos en producción.
- La imagen corre como usuario no root y parte de una imagen slim.
- Auditoría reproducible: `poetry run pip-audit`. El workflow CI la ejecuta en cada cambio. Al 2026-08-12 existe el hallazgo `PYSEC-2026-1325` en `ecdsa`, transitivo de `python-jose`, sin versión corregida publicada por la herramienta. CI falla para mantenerlo visible; debe revisarse en cada release y sustituir la dependencia/JWT si persiste. La evidencia se genera en el log de GitHub Actions.
- Para producción: rotar `JWT_SECRET`, usar HTTPS detrás de proxy, rate limiting/WAF y un proveedor OAuth/OIDC en lugar del endpoint demo de token.
