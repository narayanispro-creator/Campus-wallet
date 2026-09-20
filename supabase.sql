create table public.expenses (
 id bigint generated always as identity primary key,
 user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
 title text not null check(length(trim(title)) between 1 and 100),
 amount bigint not null check(amount between 1 and 1000000000),
 category text not null check(category in ('Food & drinks','Transport','Study','Shopping','Rent & bills','Entertainment','Other')),
 spent_on date not null,
 notes text not null default '' check(length(notes)<=500)
);
create index expenses_user_date on public.expenses(user_id,spent_on);
create table public.budgets (
 user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
 month text not null check(month ~ '^[0-9]{4}-(0[1-9]|1[0-2])$'),
 amount bigint not null check(amount between 1 and 1000000000),
 primary key(user_id,month)
);
alter table public.expenses enable row level security;
alter table public.budgets enable row level security;
create policy expenses_owner on public.expenses for all to authenticated using ((select auth.uid())=user_id) with check ((select auth.uid())=user_id);
create policy budgets_owner on public.budgets for all to authenticated using ((select auth.uid())=user_id) with check ((select auth.uid())=user_id);
revoke all on public.expenses,public.budgets from anon;
grant select,insert,update,delete on public.expenses,public.budgets to authenticated;
grant usage,select on sequence public.expenses_id_seq to authenticated;
