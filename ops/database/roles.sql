-- Run as the database owner/admin, connected to the explicitly named TARGET database.
-- psql --set=ON_ERROR_STOP=1 --set=target_database=... --set=operator_role=fpl_forge_operator --set=web_role=fpl_forge_web --file=ops/database/roles.sql
-- Creates NOLOGIN group roles. Provision real login credentials separately in your secret store.
\set ON_ERROR_STOP on
\if :{?target_database}
\else
  \echo 'Set target_database explicitly.'
  DO $$ BEGIN RAISE EXCEPTION 'Invalid role configuration; see preceding message'; END $$;
\endif
\if :{?operator_role}
\else
  \echo 'Set operator_role explicitly.'
  DO $$ BEGIN RAISE EXCEPTION 'Invalid role configuration; see preceding message'; END $$;
\endif
\if :{?web_role}
\else
  \echo 'Set web_role explicitly.'
  DO $$ BEGIN RAISE EXCEPTION 'Invalid role configuration; see preceding message'; END $$;
\endif
SELECT current_database() = :'target_database' AND :'operator_role' <> :'web_role' AS correct_target \gset
\if :correct_target
\else
  \echo 'Wrong target database or roles are identical; refusing grants.'
  DO $$ BEGIN RAISE EXCEPTION 'Invalid role configuration; see preceding message'; END $$;
\endif
BEGIN;
SELECT format('CREATE ROLE %I NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION', :'operator_role')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname=:'operator_role') \gexec
SELECT format('CREATE ROLE %I NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION', :'web_role')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname=:'web_role') \gexec
-- Reject reused privileged roles or inherited privilege memberships. These are
-- dedicated NOLOGIN group roles, not general administrator or personal logins.
SELECT NOT EXISTS (
  SELECT 1 FROM pg_roles
  WHERE rolname IN (:'web_role', :'operator_role')
    AND (rolsuper OR rolcreatedb OR rolcreaterole OR rolreplication OR rolcanlogin OR rolbypassrls OR left(rolname,3)='pg_')
) AND NOT EXISTS (
  SELECT 1 FROM pg_auth_members m JOIN pg_roles r ON r.oid=m.member
  WHERE r.rolname IN (:'web_role', :'operator_role')
) AND NOT EXISTS (
  SELECT 1 FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
  WHERE n.nspname='public' AND p.prosecdef
) AS roles_safe \gset
\if :roles_safe
\else
  \echo 'Roles must be unprivileged NOLOGIN groups with no inherited memberships; public SECURITY DEFINER functions require separate review.'
  DO $$ BEGIN RAISE EXCEPTION 'Invalid role configuration; see preceding message'; END $$;
\endif
REVOKE ALL ON DATABASE :"target_database" FROM PUBLIC;
REVOKE ALL ON DATABASE :"target_database" FROM :"web_role";
GRANT CONNECT ON DATABASE :"target_database" TO :"operator_role", :"web_role";
ALTER DATABASE :"target_database" OWNER TO :"operator_role";
REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM :"web_role";
ALTER SCHEMA public OWNER TO :"operator_role";
GRANT USAGE ON SCHEMA public TO :"web_role";
GRANT ALL ON SCHEMA public TO :"operator_role";
SELECT format('ALTER TABLE %I.%I OWNER TO %I', schemaname, tablename, :'operator_role')
FROM pg_tables WHERE schemaname='public' \gexec
SELECT format('ALTER SEQUENCE %I.%I OWNER TO %I', sequence_schema, sequence_name, :'operator_role')
FROM information_schema.sequences WHERE sequence_schema='public' \gexec
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM PUBLIC;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM :"web_role";
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM :"web_role";
GRANT SELECT ON ALL TABLES IN SCHEMA public TO :"web_role";
ALTER DEFAULT PRIVILEGES FOR ROLE :"operator_role"
  REVOKE ALL ON TABLES FROM PUBLIC, :"web_role";
ALTER DEFAULT PRIVILEGES FOR ROLE :"operator_role"
  REVOKE ALL ON SEQUENCES FROM PUBLIC, :"web_role";
ALTER DEFAULT PRIVILEGES FOR ROLE :"operator_role" IN SCHEMA public
  REVOKE ALL ON TABLES FROM PUBLIC, :"web_role";
ALTER DEFAULT PRIVILEGES FOR ROLE :"operator_role" IN SCHEMA public
  REVOKE ALL ON SEQUENCES FROM PUBLIC, :"web_role";
ALTER DEFAULT PRIVILEGES FOR ROLE :"operator_role" IN SCHEMA public
  GRANT SELECT ON TABLES TO :"web_role";
-- No sequence grants are needed for a read-only web application.
-- Operator sessions must SET ROLE to operator_role before migrations/imports, ensuring
-- newly created objects use these ownership/default privileges.

COMMIT;
