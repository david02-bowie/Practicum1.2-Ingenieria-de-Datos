-- Consulta 1: Matrícula total por provincia en el año lectivo más reciente
SELECT 
    "Provincia",
    SUM("Matricula_Total") AS matricula_total
FROM amie
WHERE "Año lectivo" = '2023-2024 Fin'
GROUP BY "Provincia"
ORDER BY matricula_total DESC;


-- Consulta 2: Instituciones fiscales vs. particulares por área urbana/rural en Loja
SELECT 
    "Área",
    "Sostenimiento",
    COUNT(DISTINCT "AMIE") AS total_instituciones
FROM amie
WHERE "Año lectivo" = '2023-2024 Fin'
  AND "Provincia" = 'LOJA'
  AND "Sostenimiento" IN ('FISCAL', 'PARTICULAR')
GROUP BY "Área", "Sostenimiento"
ORDER BY "Área", "Sostenimiento";


-- Consulta 3: Evolución de instituciones activas en Ecuador entre 2015 y 2024
SELECT 
    "Año lectivo",
    COUNT(DISTINCT "AMIE") AS instituciones_activas
FROM amie
WHERE "Año lectivo" IN (
    '2015-2016 Fin',
    '2016-2017 Fin',
    '2017-2018 Fin',
    '2018-2019 Fin',
    '2019-2020 Fin',
    '2020-2021 Fin',
    '2021-2022 Fin',
    '2022-2023 Fin',
    '2023-2024 Fin'
)
GROUP BY "Año lectivo"
ORDER BY "Año lectivo";


-- Consulta 4: Total nacional de matrícula en 2023-2024
SELECT 
    SUM("Matricula_Total") AS total_nacional
FROM amie
WHERE "Año lectivo" = '2023-2024 Fin';


-- Consulta 5: Total de registros cargados en SQLite
SELECT 
    COUNT(*) AS total_registros
FROM amie;