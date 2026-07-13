# AquaRisk

Aplicación web en React para monitorear lluvia, ubicación y riesgo de inundación.

## Stack

- React + Vite + TypeScript
- MapLibre GL JS para mapas
- TanStack Query para consultas climáticas
- Zustand para estado local
- Vite PWA para instalar en Android
- Open-Meteo como fuente meteorológica inicial
- Open-Meteo Flood API para caudal de ríos cercano
- Supabase preparado para backend, PostGIS y alertas

## Comandos

```bash
npm install
npm run dev
npm run build
npm run lint
```

## Qué hace ahora

- Usa GPS del navegador.
- Consulta clima real con Open-Meteo.
- Traduce milímetros de lluvia a lenguaje claro: ligera, moderada, fuerte.
- Indica si conviene salir o no.
- Detecta posible tormenta eléctrica con códigos meteorológicos.
- Calcula duración estimada de lluvia en las próximas horas.
- Muestra puntos cercanos consultados con datos reales. Ya no dibuja rectángulos simulados.
- Consulta caudal de río cercano con Open-Meteo Flood API.
- Explica qué significa 1 mm de lluvia.
- Busca puntos de apoyo cercanos con OpenStreetMap/Nominatim.
- Separa riesgo actual, zonas vulnerables cercanas y aviso futuro.
- Permite activar alertas del dispositivo sin crear cuenta.

## Supabase

El backend no está desplegado todavía porque faltan las claves del proyecto.

Archivos incluidos:

- `.env.example`
- `src/lib/supabase.ts`
- `supabase/migrations/001_initial_aquarisk_schema.sql`
- `supabase/migrations/002_emergency_features_no_login.sql`
- `supabase/seed_tapachula_demo.sql`
- `supabase/functions/risk-monitor/index.ts`

Para conectarlo:

1. Crear un proyecto en Supabase.
2. Copiar `.env.example` a `.env`.
3. Agregar `VITE_SUPABASE_URL` y `VITE_SUPABASE_ANON_KEY`.
4. Ejecutar la migración SQL en Supabase.
5. Ejecutar también la migración `002_emergency_features_no_login.sql`.
6. Opcional: ejecutar `seed_tapachula_demo.sql` para cargar puntos de apoyo y
   zonas demo de Tapachula.
7. Desplegar la Edge Function `risk-monitor`.

La idea del backend ya no depende de login. Sirve para suscripciones anónimas de
alerta, zonas vulnerables oficiales y puntos seguros administrados por la app.

## Nota importante

Open-Meteo da pronóstico meteorológico por coordenadas y el Flood API da caudal modelado de ríos. OpenStreetMap ayuda a encontrar puntos de apoyo cercanos, pero no sustituye instrucciones oficiales. Las zonas de `seed_tapachula_demo.sql` son datos iniciales para una demo académica y deben validarse antes de usarse como zonas oficiales. Para riesgo oficial de inundación urbana se deben cargar capas reales en `official_risk_zones`, por ejemplo datos de protección civil, zonas históricas de inundación o mapas municipales.
