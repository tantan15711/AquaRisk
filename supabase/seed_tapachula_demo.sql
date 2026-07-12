insert into public.safe_locations (name, kind, source, point, notes)
select *
from (
  values
    (
      'Proteccion Civil Tapachula',
      'Proteccion civil',
      'OpenStreetMap / Nominatim',
      'SRID=4326;POINT(-92.2912304 14.8673796)'::geography,
      'Punto de apoyo para coordinacion de emergencias; confirmar disponibilidad.'
    ),
    (
      'Heroico Cuerpo de Bomberos de Tapachula',
      'Bomberos',
      'OpenStreetMap / Nominatim',
      'SRID=4326;POINT(-92.2697532 14.9033496)'::geography,
      'Punto de apoyo ante lluvia intensa, accidentes o rescate.'
    ),
    (
      'Hospital General',
      'Hospital',
      'OpenStreetMap / Nominatim',
      'SRID=4326;POINT(-92.2906029 14.8867801)'::geography,
      'Atencion medica; no necesariamente refugio.'
    ),
    (
      'Hospital Metropolitano del Sur',
      'Hospital',
      'OpenStreetMap / Nominatim',
      'SRID=4326;POINT(-92.2570760 14.9015388)'::geography,
      'Atencion medica; no necesariamente refugio.'
    ),
    (
      'Escuela Preparatoria Eduardo Javier Albores Gonzalez',
      'Escuela',
      'OpenStreetMap / Nominatim',
      'SRID=4326;POINT(-92.2426755 14.8946369)'::geography,
      'Posible punto comunitario; validar con autoridad local.'
    ),
    (
      'Escuela Primaria Teodomiro Palacios',
      'Escuela',
      'OpenStreetMap / Nominatim',
      'SRID=4326;POINT(-92.2549840 14.9327172)'::geography,
      'Posible punto comunitario; validar con autoridad local.'
    )
) as seed(name, kind, source, point, notes)
where not exists (
  select 1
  from public.safe_locations existing
  where lower(existing.name) = lower(seed.name)
);

insert into public.official_risk_zones (name, source, risk_level, polygon)
select *
from (
  values
    (
      'Corredor Rio Cahoacan - oriente de Tapachula',
      'Demo educativa AquaRisk; validar con Proteccion Civil',
      'alto',
      st_geomfromtext(
        'POLYGON((-92.2420 14.9010,-92.2250 14.9010,-92.2250 14.8790,-92.2420 14.8790,-92.2420 14.9010))',
        4326
      )
    ),
    (
      'Zona baja sur-poniente',
      'Demo educativa AquaRisk; validar con Proteccion Civil',
      'medio',
      st_geomfromtext(
        'POLYGON((-92.3030 14.8920,-92.2820 14.8920,-92.2820 14.8720,-92.3030 14.8720,-92.3030 14.8920))',
        4326
      )
    ),
    (
      'Canales urbanos zona centro-sur',
      'Demo educativa AquaRisk; validar con Proteccion Civil',
      'medio',
      st_geomfromtext(
        'POLYGON((-92.2760 14.9160,-92.2520 14.9160,-92.2520 14.8950,-92.2760 14.8950,-92.2760 14.9160))',
        4326
      )
    )
) as seed(name, source, risk_level, polygon)
where not exists (
  select 1
  from public.official_risk_zones existing
  where lower(existing.name) = lower(seed.name)
);
