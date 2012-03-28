--
-- Global settings
--

SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = off;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET escape_string_warning = off;

SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;


--
-- user
--

CREATE TABLE auth_user (
    id integer PRIMARY KEY,
    username character varying(30) NOT NULL,
    password character varying(142) NOT NULL, -- 12 + 1 + 128
    last_login timestamp with time zone NOT NULL,
    date_joined timestamp with time zone NOT NULL
);

-- one create method for serial data type
CREATE SEQUENCE auth_user_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;

ALTER SEQUENCE auth_user_id_seq NO CYCLE OWNED BY auth_user.id;
ALTER TABLE auth_user ALTER COLUMN id SET DEFAULT nextval('auth_user_id_seq'::regclass);


--
-- group
--

CREATE TABLE auth_group (
    id serial PRIMARY KEY,
    name character varying(80) NOT NULL
);


--
-- permission
--

CREATE TABLE auth_permission (
    id serial PRIMARY KEY,
    name character varying(50) NOT NULL,
    codename character varying(100) NOT NULL
);


--
-- user_groups
--

CREATE TABLE user_groups (
    id serial PRIMARY KEY,
    user_id integer REFERENCES auth_user(id),
    group_id integer REFERENCES auth_group(id)
);


--
-- user_permissions
--

CREATE TABLE user_permissions (
    id serial PRIMARY KEY,
    user_id integer REFERENCES auth_user(id),
    permission_id integer REFERENCES auth_permission(id)
);


--
-- group_permissions
--

CREATE TABLE group_permissions (
    id serial PRIMARY KEY,
    group_id integer REFERENCES auth_group(id),
    permission_id integer REFERENCES auth_permission(id)
);


--
-- session
--

CREATE TABLE auth_session (
    session_key character varying(40) PRIMARY KEY,
    session_data text,
    expire_date timestamp with time zone NOT NULL
);


--
-- user_profile
--

CREATE TABLE user_profile (
    id serial PRIMARY KEY,
    user_id integer REFERENCES auth_user(id) ON DELETE CASCADE,
    first_name character varying(32),
    last_name character varying(32),
    gender boolean,

    locale character varying(12),

    email character varying(64),
    
    UNIQUE (user_id)
);


--
-- appliance_catalog
--

CREATE TABLE appliance_catalog (
    id serial PRIMARY KEY,
    name character varying(64) NOT NULL,
    summary character varying(256),
    description text,
    position integer DEFAULT 0,
    created timestamp with time zone NOT NULL,
    updated timestamp with time zone NOT NULL
);


--
-- appliance
--

CREATE TABLE appliance (
    id serial PRIMARY KEY,
    name character varying(64) NOT NULL,
    summary character varying(256),
    description text,

    user_id integer REFERENCES auth_user(id),
    catalog_id integer REFERENCES appliance_catalog(id),

    logoname character varying(36),
    filesize integer NOT NULL,
    checksum character varying(32) NOT NULL, -- md5 value

    is_useable boolean DEFAULT False,
    popularity integer DEFAULT 0,

    created timestamp with time zone NOT NULL,
    updated timestamp with time zone NOT NULL
);


--
-- app_catalog
--

CREATE TABLE application_catalog (
    id serial PRIMARY KEY,
    name character varying(64) NOT NULL,
    summary character varying(256),
    description text,
    user_id integer REFERENCES auth_user(id),
    position integer DEFAULT 0,
    created timestamp with time zone NOT NULL,
    updated timestamp with time zone NOT NULL
);


--
-- node
--

CREATE TABLE node (
    id serial PRIMARY KEY,
    hostname character varying(64),
    key character varying(128),
    ip inet NOT NULL,
-- should bind with some authenticate method
    arch integer NOT NULL,
    status integer NOT NULL,
    isenable boolean DEFAULT False, /* TODO */
    memory integer NOT NULL,
    cpus integer NOT NULL,
    cpu_model character varying(64) NOT NULL,
    cpu_mhz integer NOT NULL,
    created timestamp with time zone NOT NULL,
    updated timestamp with time zone NOT NULL
);

--
-- instance
--

CREATE TABLE instance (
    id serial PRIMARY KEY,
    name character varying(64) NOT NULL,
    key character varying(128),
    summary character varying(256),
    description text,
    logo character varying(64), -- 'instance_logo_' + md5 + 'suffix'

    cpus integer DEFAULT 1,
    memory integer DEFAULT 256,  -- 256M

    user_id integer REFERENCES auth_user(id) NOT NULL,
    appliance_id integer REFERENCES appliance(id) NOT NULL,
    node_id integer REFERENCES node(id),
-- should bind with node !

    ip inet,                -- unique ?
    mac macaddr UNIQUE,

    status integer NOT NULL, -- default is stop ?

    config character varying(256),

    created timestamp with time zone NOT NULL,
    updated timestamp with time zone NOT NULL
);


--
-- job
--

CREATE TABLE job (
    id serial PRIMARY KEY,
    user_id integer REFERENCES auth_user(id) NOT NULL,
    status integer NOT NULL,

    target_type integer NOT NULL,
    target_id integer NOT NULL,

    action integer NOT NULL,

    started timestamp with time zone,
    ended timestamp with time zone,

    created timestamp with time zone NOT NULL
);


--
-- wiki_catalog
--

CREATE TABLE wiki_catalog (
    id serial PRIMARY KEY,
    name character varying(64) NOT NULL,
    summary character varying(256),
    description text,
    position integer DEFAULT 0,
    created timestamp with time zone NOT NULL,
    updated timestamp with time zone NOT NULL
);


--
-- topic
--

CREATE TABLE topic (
    id serial PRIMARY KEY,
    name character varying(256) NOT NULL,

    user_id integer REFERENCES auth_user(id) NOT NULL,
    catalog_id integer REFERENCES wiki_catalog(id) NOT NULL,

    body text NOT NULL,
    body_html text NOT NULL,

    user_ip inet NOT NULL,
    views integer DEFAULT 0,
    closed boolean DEFAULT False,

    created timestamp with time zone NOT NULL,
    updated timestamp with time zone NOT NULL
);


--
-- Insert default values
--

-- username: admin, password: admin
INSERT INTO auth_user (username, date_joined, last_login, password) VALUES ('admin', 'now', 'now', 'ecc1234328f6$9537a8be9eb122ab7fb7d215838e159df9186744a6ae40935572be00f02f10bf0c0cf52deb45721e42563db53df0efa78b405ffdecd6583df281479400aea3cd');

INSERT INTO user_profile (user_id, first_name, last_name, locale, email) VALUES (1, 'Admin', 'System Manager', 'zh_CN', 'admin@luoyun.co');

-- admin role
INSERT INTO auth_permission (name, codename) VALUES ('Administrator', 'admin');

INSERT INTO user_permissions (user_id, permission_id) VALUES (1, 1);


--
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--

--REVOKE ALL ON SCHEMA public FROM PUBLIC;
--REVOKE ALL ON SCHEMA public FROM postgres;
--GRANT ALL ON SCHEMA public TO postgres;
--GRANT ALL ON SCHEMA public TO PUBLIC;
