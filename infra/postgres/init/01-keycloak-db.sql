-- ADR-001 §16.3: Keycloak usa base de datos y credenciales SEPARADAS de los
-- datos de negocio de PIP-GAMS (misma instancia PostgreSQL, base propia).
-- Se ejecuta una sola vez al inicializar el volumen (docker-entrypoint-initdb.d).
CREATE DATABASE keycloak;
CREATE USER keycloak_user WITH PASSWORD 'changeme-keycloak-db';
ALTER DATABASE keycloak OWNER TO keycloak_user;
GRANT ALL PRIVILEGES ON DATABASE keycloak TO keycloak_user;
