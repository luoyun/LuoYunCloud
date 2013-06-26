BEGIN;

-- Running upgrade None -> 4ef11bcd5a0a

CREATE TABLE auth_key (
    id SERIAL NOT NULL, 
    auth_key VARCHAR(256), 
    auth_data VARCHAR(1024), 
    expire_date TIMESTAMP WITHOUT TIME ZONE, 
    PRIMARY KEY (id)
);

CREATE TABLE gateway (
    id SERIAL NOT NULL, 
    name VARCHAR(128), 
    description TEXT, 
    ip VARCHAR(60), 
    netmask VARCHAR(60), 
    start INTEGER, 
    "end" INTEGER, 
    exclude_ports TEXT, 
    created TIMESTAMP WITHOUT TIME ZONE, 
    updated TIMESTAMP WITHOUT TIME ZONE, 
    PRIMARY KEY (id), 
    UNIQUE (ip)
);

CREATE TABLE site_config (
    id SERIAL NOT NULL, 
    key VARCHAR(256), 
    value TEXT, 
    PRIMARY KEY (id)
);

CREATE TABLE registration_apply (
    id SERIAL NOT NULL, 
    email VARCHAR(32), 
    key VARCHAR(128), 
    created TIMESTAMP WITHOUT TIME ZONE, 
    PRIMARY KEY (id)
);

CREATE TABLE storagepool (
    id SERIAL NOT NULL, 
    name VARCHAR(128), 
    description TEXT, 
    total INTEGER, 
    used INTEGER, 
    created TIMESTAMP WITHOUT TIME ZONE, 
    updated TIMESTAMP WITHOUT TIME ZONE, 
    PRIMARY KEY (id)
);

CREATE TABLE site_locale_config (
    id SERIAL NOT NULL, 
    language_id INTEGER, 
    key VARCHAR(256), 
    value TEXT, 
    PRIMARY KEY (id), 
    FOREIGN KEY(language_id) REFERENCES language (id)
);

CREATE TABLE public_key (
    id SERIAL NOT NULL, 
    user_id INTEGER, 
    name VARCHAR(128), 
    data VARCHAR(1024), 
    isdefault BOOLEAN, 
    created TIMESTAMP WITHOUT TIME ZONE, 
    updated TIMESTAMP WITHOUT TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES auth_user (id)
);

CREATE TABLE resource (
    id SERIAL NOT NULL, 
    user_id INTEGER, 
    type INTEGER, 
    size INTEGER, 
    created TIMESTAMP WITHOUT TIME ZONE, 
    updated TIMESTAMP WITHOUT TIME ZONE, 
    effect_date TIMESTAMP WITHOUT TIME ZONE, 
    expired_date TIMESTAMP WITHOUT TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES auth_user (id)
);

CREATE TABLE auth_openid (
    id SERIAL NOT NULL, 
    user_id INTEGER, 
    openid VARCHAR(256), 
    type INTEGER, 
    created TIMESTAMP WITHOUT TIME ZONE, 
    updated TIMESTAMP WITHOUT TIME ZONE, 
    config TEXT, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES auth_user (id)
);

CREATE TABLE user_domain (
    id SERIAL NOT NULL, 
    domain VARCHAR(256), 
    user_id INTEGER, 
    instance_id INTEGER, 
    created TIMESTAMP WITHOUT TIME ZONE, 
    updated TIMESTAMP WITHOUT TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(instance_id) REFERENCES instance (id), 
    FOREIGN KEY(user_id) REFERENCES auth_user (id), 
    UNIQUE (domain)
);

CREATE TABLE storage (
    id SERIAL NOT NULL, 
    size INTEGER, 
    pool_id INTEGER, 
    instance_id INTEGER, 
    created TIMESTAMP WITHOUT TIME ZONE, 
    updated TIMESTAMP WITHOUT TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(instance_id) REFERENCES instance (id), 
    FOREIGN KEY(pool_id) REFERENCES storagepool (id)
);

CREATE TABLE port_mapping (
    id SERIAL NOT NULL, 
    gateway_port INTEGER, 
    gateway_id INTEGER, 
    ip_port INTEGER, 
    ip_id INTEGER, 
    created TIMESTAMP WITHOUT TIME ZONE, 
    updated TIMESTAMP WITHOUT TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(gateway_id) REFERENCES gateway (id), 
    FOREIGN KEY(ip_id) REFERENCES ippool (id)
);

DROP TABLE apply_user;

DROP TABLE user_permissions;

ALTER TABLE auth_user ADD COLUMN email_valid BOOLEAN;

ALTER TABLE auth_user ADD COLUMN notice INTEGER;

ALTER TABLE auth_user ADD COLUMN last_name VARCHAR(30);

ALTER TABLE auth_user ADD COLUMN is_locked BOOLEAN;

ALTER TABLE auth_user ADD COLUMN gender BOOLEAN;

ALTER TABLE auth_user ADD COLUMN is_active BOOLEAN;

ALTER TABLE auth_user ADD COLUMN first_name VARCHAR(30);

ALTER TABLE auth_user ADD COLUMN language_id INTEGER;

ALTER TABLE auth_user ADD COLUMN is_superuser BOOLEAN;

ALTER TABLE auth_user ADD COLUMN is_staff BOOLEAN;

ALTER TABLE auth_user ADD COLUMN nickname VARCHAR(30);

ALTER TABLE auth_user ADD COLUMN email VARCHAR(64);

ALTER TABLE auth_user DROP COLUMN notification;

ALTER TABLE auth_user DROP COLUMN islocked;

ALTER TABLE auth_user DROP COLUMN last_entry;

ALTER TABLE auth_user DROP COLUMN description;

ALTER TABLE instance DROP COLUMN subdomain;

ALTER TABLE user_profile ADD COLUMN memory_used INTEGER;

ALTER TABLE user_profile ADD COLUMN updated TIMESTAMP WITHOUT TIME ZONE;

ALTER TABLE user_profile ADD COLUMN cpu_total INTEGER;

ALTER TABLE user_profile ADD COLUMN created TIMESTAMP WITHOUT TIME ZONE;

ALTER TABLE user_profile ADD COLUMN coins INTEGER;

ALTER TABLE user_profile ADD COLUMN memory_total INTEGER;

ALTER TABLE user_profile ADD COLUMN storage_total INTEGER;

ALTER TABLE user_profile ADD COLUMN instance_total INTEGER;

ALTER TABLE user_profile ADD COLUMN storage_used INTEGER;

ALTER TABLE user_profile ADD COLUMN cpu_used INTEGER;

ALTER TABLE user_profile ADD COLUMN instance_used INTEGER;

ALTER TABLE user_profile DROP COLUMN first_name;

ALTER TABLE user_profile DROP COLUMN last_name;

ALTER TABLE user_profile DROP COLUMN locale;

ALTER TABLE user_profile DROP COLUMN gender;

ALTER TABLE user_profile DROP COLUMN storage;

ALTER TABLE user_profile DROP COLUMN cpus;

ALTER TABLE user_profile DROP COLUMN instances;

ALTER TABLE user_profile DROP COLUMN memory;

ALTER TABLE user_profile DROP COLUMN email;


ALTER TABLE auth_user ALTER COLUMN id SET DEFAULT nextval('auth_user_id_seq'::regclass);


COMMIT;

