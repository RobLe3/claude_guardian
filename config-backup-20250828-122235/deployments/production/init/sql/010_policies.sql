insert into policy (id, level, description, snippet) values
('polMin01','warn','Check access to sensitive paths','deny if path like /etc/%'),
('polNet01','block','Block outbound network calls unless allowlisted','deny if outbound and not allowlisted')
on conflict (id) do nothing;
