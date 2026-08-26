# Conceptos — Issue 05

Seed — 15 min; fixture — 15 min; idempotencia — 20 min; orden de inserción por FK — 20 min; datos sintéticos y secretos — 15 min; transacción atómica — 20 min.

El seed no reemplaza una migración ni debe contener contraseñas reales. Usa identificadores o claves naturales estables para detectar registros ya creados y una única transacción para evitar estados parciales.

