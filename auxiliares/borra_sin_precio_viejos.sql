.headers on
.mode csv
.output data.csv

ATTACH DATABASE 'monitoreo_juegos.db' AS juegos_db;

WITH precios_recientes AS (
    SELECT id_juego
    FROM precios
    WHERE fecha >= date('now', '-2 years')
    GROUP BY id_juego
)

-- SELECT *
-- FROM juegos_db.juegos
-- WHERE id_juego NOT IN (SELECT id_juego FROM precios_recientes);

DELETE FROM juegos_db.juegos
WHERE id_juego NOT IN (SELECT id_juego FROM precios_recientes);