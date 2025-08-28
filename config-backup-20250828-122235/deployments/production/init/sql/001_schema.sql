create table if not exists audit_event (
  id bigserial primary key,
  ts timestamptz default now(),
  actor text not null,
  kind text not null,
  label text not null,
  risk numeric not null,
  details jsonb
);

create table if not exists policy (
  id text primary key,
  level text not null,
  description text,
  snippet text,
  updated_at timestamptz default now()
);
