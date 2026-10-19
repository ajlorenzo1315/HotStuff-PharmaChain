# Dominio farmacéutico

| Archivo | Función |
| --- | --- |
| `models.py` | Organizaciones, roles y tipos de operación |
| `transactions.py` | Transacciones del libro mayor |
| `state.py` | Estado de lotes y validación de reglas |
| `crypto.py` | Claves y funciones criptográficas |
| `audit.py` | Información de auditoría |

El caso de uso registra lotes y transferencias entre organizaciones.
Las reglas de autorización y custodia pertenecen al dominio, no al
algoritmo de consenso BFT.

La firma digital acredita el uso de una clave; no prueba la entrega
física de un medicamento.

```bash
python -m pytest tests/test_pharmachain_domain.py -v
```
