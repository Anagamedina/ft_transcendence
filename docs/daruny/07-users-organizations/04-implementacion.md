# Implementación — Issue 07

1. Revisar modelos y decidir la forma canónica de normalizar emails.
2. Implementar `get_by_email`, `create_user`, `get_by_id` de usuario y organización.
3. Añadir o verificar índice/constraint único en email y FK de organización.
4. Convertir violaciones de integridad en un error que Ana pueda mapear.
5. Probar creación, búsqueda, organización inexistente y duplicado, incluyendo rollback.
6. Documentar la interfaz; el hash corresponde al service de Ana.
