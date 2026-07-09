-- Capa Gold: vistas analíticas para Power BI

DROP VIEW IF EXISTS gold_pib_tendencia;
DROP VIEW IF EXISTS gold_petroleo_30dias;
DROP VIEW IF EXISTS gold_vab_provincia;
DROP VIEW IF EXISTS gold_bachilleres_provincia;

CREATE VIEW gold_pib_tendencia AS
SELECT 
    t.anio,
    m.pib_real_musd,
    m.pib_percapita_nominal,
    m.variacion_pib_pct,
    CASE 
        WHEN m.variacion_pib_pct > 2 THEN 'Crecimiento fuerte'
        WHEN m.variacion_pib_pct > 0 THEN 'Crecimiento moderado'
        WHEN m.variacion_pib_pct = 0 THEN 'Estancamiento'
        ELSE 'Contracción'
    END AS clasificacion
FROM fact_macro_anual m
INNER JOIN dim_tiempo t 
    ON m.id_tiempo = t.id_tiempo;

CREATE VIEW gold_petroleo_30dias AS
SELECT
    fecha,
    precio_petroleo_wti,
    riesgo_pais_pb,
    AVG(precio_petroleo_wti) OVER (
        ORDER BY fecha
        ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) AS promedio_petroleo_30dias
FROM fact_indicadores_diarios;

CREATE VIEW gold_vab_provincia AS
SELECT
    g.provincia,
    v.anio,
    v.ciiu,
    SUM(v.vab_miles_usd) AS total_vab_miles_usd
FROM fact_vab v
INNER JOIN dim_geografia g
    ON v.id_geo = g.id_geo
GROUP BY 
    g.provincia,
    v.anio,
    v.ciiu;

CREATE VIEW gold_bachilleres_provincia AS
SELECT
    g.provincia,
    m.anio_lectivo,
    m.sostenimiento,
    SUM(m.total_estudiantes) AS total_bachilleres
FROM fact_mineduc_bachillerato m
INNER JOIN dim_geografia g
    ON m.id_geo = g.id_geo
GROUP BY
    g.provincia,
    m.anio_lectivo,
    m.sostenimiento;