-- Description: SQL script to create the boilerplate_db database, schemas, and users. ONLY FOR LOCAl DEVELOPMENT AND TESTING.
CREATE SCHEMA sample_schema
    AUTHORIZATION db_master_admin;

CREATE USER db_user WITH
  LOGIN
  NOSUPERUSER
  INHERIT
  NOCREATEDB
  NOCREATEROLE
  NOREPLICATION;

ALTER USER db_user WITH PASSWORD 'db_user_password';

GRANT TEMPORARY ON DATABASE app_db TO db_user;

GRANT TEMPORARY, CONNECT ON DATABASE app_db TO PUBLIC;

GRANT ALL ON DATABASE app_db TO db_master_admin;

GRANT db_user to db_master_admin;

GRANT ALL ON SCHEMA sample_schema TO db_user;

GRANT ALL ON SCHEMA sample_schema TO db_master_admin WITH GRANT OPTION;
