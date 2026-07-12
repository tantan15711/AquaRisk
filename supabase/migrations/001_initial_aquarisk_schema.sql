create extension if not exists postgis;
create extension if not exists pgcrypto;

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  full_name text,
  created_at timestamptz not null default now()
);

create table if not exists public.device_tokens (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  token text not null,
  platform text not null default 'web',
  created_at timestamptz not null default now(),
  unique (user_id, token)
);

create table if not exists public.monitored_locations (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade,
  name text not null,
  point geography(Point, 4326) not null,
  radius_m integer not null default 1500,
  is_active boolean not null default true,
  created_at timestamptz not null default now()
);

create table if not exists public.weather_snapshots (
  id uuid primary key default gen_random_uuid(),
  source text not null default 'open-meteo',
  point geography(Point, 4326) not null,
  rain_now_mm numeric not null default 0,
  rain_next_6h_mm numeric not null default 0,
  probability_max integer not null default 0,
  weather_code integer,
  thunder_likely boolean not null default false,
  fetched_at timestamptz not null default now()
);

create table if not exists public.risk_assessments (
  id uuid primary key default gen_random_uuid(),
  monitored_location_id uuid references public.monitored_locations(id) on delete cascade,
  weather_snapshot_id uuid references public.weather_snapshots(id) on delete set null,
  risk_level text not null check (risk_level in ('bajo', 'medio', 'alto', 'critico')),
  score integer not null check (score between 0 and 100),
  rain_label text not null,
  recommendation text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.alerts (
  id uuid primary key default gen_random_uuid(),
  monitored_location_id uuid references public.monitored_locations(id) on delete cascade,
  risk_assessment_id uuid references public.risk_assessments(id) on delete set null,
  title text not null,
  body text not null,
  severity text not null check (severity in ('info', 'medio', 'alto', 'critico')),
  sent_at timestamptz,
  created_at timestamptz not null default now()
);

create table if not exists public.official_risk_zones (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  source text not null,
  risk_level text not null check (risk_level in ('bajo', 'medio', 'alto', 'critico')),
  polygon geometry(Polygon, 4326) not null,
  updated_at timestamptz not null default now()
);

create or replace view public.monitored_location_points as
select
  id,
  user_id,
  name,
  st_y(point::geometry) as latitude,
  st_x(point::geometry) as longitude,
  radius_m,
  is_active
from public.monitored_locations;

alter table public.profiles enable row level security;
alter table public.device_tokens enable row level security;
alter table public.monitored_locations enable row level security;
alter table public.weather_snapshots enable row level security;
alter table public.risk_assessments enable row level security;
alter table public.alerts enable row level security;
alter table public.official_risk_zones enable row level security;

create policy "profiles are owner readable"
on public.profiles for select
using (auth.uid() = id);

create policy "device tokens are owner managed"
on public.device_tokens for all
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

create policy "monitored locations are owner managed"
on public.monitored_locations for all
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

create policy "official zones are public readable"
on public.official_risk_zones for select
using (true);

create policy "weather snapshots are authenticated readable"
on public.weather_snapshots for select
to authenticated
using (true);

create policy "risk assessments are owner readable"
on public.risk_assessments for select
using (
  exists (
    select 1
    from public.monitored_locations ml
    where ml.id = monitored_location_id
      and ml.user_id = auth.uid()
  )
);

create policy "alerts are owner readable"
on public.alerts for select
using (
  exists (
    select 1
    from public.monitored_locations ml
    where ml.id = monitored_location_id
      and ml.user_id = auth.uid()
  )
);
