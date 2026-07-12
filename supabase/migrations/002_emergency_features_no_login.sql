create table if not exists public.alert_subscriptions (
  id uuid primary key default gen_random_uuid(),
  device_label text not null default 'Dispositivo AquaRisk',
  point geography(Point, 4326) not null,
  radius_m integer not null default 1500,
  min_score integer not null default 58 check (min_score between 0 and 100),
  is_active boolean not null default true,
  created_at timestamptz not null default now()
);

create table if not exists public.safe_locations (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  kind text not null,
  source text not null,
  point geography(Point, 4326) not null,
  notes text,
  is_active boolean not null default true,
  updated_at timestamptz not null default now()
);

alter table public.alerts
add column if not exists alert_subscription_id uuid references public.alert_subscriptions(id) on delete cascade;

create or replace view public.alert_subscription_points as
select
  id,
  device_label,
  st_y(point::geometry) as latitude,
  st_x(point::geometry) as longitude,
  radius_m,
  min_score,
  is_active
from public.alert_subscriptions;

create or replace view public.safe_location_points as
select
  id,
  name,
  kind,
  source,
  st_y(point::geometry) as latitude,
  st_x(point::geometry) as longitude,
  notes,
  is_active
from public.safe_locations;

create or replace view public.official_risk_zone_centers as
select
  id,
  name,
  source,
  risk_level,
  st_y(st_pointonsurface(polygon)::geometry) as latitude,
  st_x(st_pointonsurface(polygon)::geometry) as longitude,
  updated_at
from public.official_risk_zones;

alter table public.alert_subscriptions enable row level security;
alter table public.safe_locations enable row level security;

create policy "alert subscriptions can be created without login"
on public.alert_subscriptions for insert
to anon, authenticated
with check (true);

create policy "safe locations are public readable"
on public.safe_locations for select
using (is_active = true);
