-- Base de datos SQLite
-- Pipeline macroentorno ecuatoriano
-- Capa Silver: tablas limpias

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS fact_mineduc_bachillerato;
DROP TABLE IF EXISTS fact_iee;
DROP TABLE IF EXISTS fact_vab;
DROP TABLE IF EXISTS fact_indicadores_diarios;
DROP TABLE IF EXISTS fact_macro_anual;
DROP TABLE IF EXISTS dim_geografia;
DROP TABLE IF EXISTS dim_tiempo;

CREATE TABLE dim_tiempo (
    id_tiempo INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL,
    anio INTEGER NOT NULL,
    mes INTEGER,
    trimestre INTEGER
);

CREATE TABLE dim_geografia (
    id_geo INTEGER PRIMARY KEY AUTOINCREMENT,
    provincia TEXT NOT NULL,
    cod_provincia INTEGER,
    canton TEXT,
    cod_canton INTEGER
);

CREATE TABLE fact_macro_anual (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_tiempo INTEGER,
    pib_real_musd REAL,
    pib_percapita_nominal REAL,
    variacion_pib_pct REAL,
    FOREIGN KEY (id_tiempo) REFERENCES dim_tiempo(id_tiempo)
);

CREATE TABLE fact_indicadores_diarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL,
    precio_petroleo_wti REAL,
    riesgo_pais_pb INTEGER
);

CREATE TABLE fact_vab (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_geo INTEGER,
    anio INTEGER,
    ciiu TEXT,
    vab_miles_usd REAL,
    FOREIGN KEY (id_geo) REFERENCES dim_geografia(id_geo)
);

CREATE TABLE fact_iee (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL,
    anio INTEGER,
    mes INTEGER,
    iee_global REAL,
    comercio REAL,
    construccion REAL,
    manufactura REAL
);

CREATE TABLE fact_mineduc_bachillerato (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_geo INTEGER,
    anio_lectivo TEXT,
    amie TEXT,
    nombre_institucion TEXT,
    nivel_educacion TEXT,
    sostenimiento TEXT,
    total_estudiantes INTEGER,
    FOREIGN KEY (id_geo) REFERENCES dim_geografia(id_geo)
);