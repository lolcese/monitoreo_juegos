CREATE TABLE sitios (
                            id_sitio INTEGER PRIMARY KEY,
                            sitio_ID TEXT NOT NULL,
                            nombre_sitio TEXT NOT NULL,
                            URL_base TEXT NOT NULL
                            );
CREATE TABLE alarmas (
                            id_alarma INTEGER PRIMARY KEY,
                            id_persona INTEGER NOT NULL,
                            BGG_id INTEGER NOT NULL,
                            sitio TEXT NOT NULL,
                            precio_alarma REAL NOT NULL,
                            fecha datetime NOT NULL
                            );
CREATE TABLE comentarios (
                            id_comentarios INTEGER PRIMARY KEY,
                            usuario TEXT NOT NULL,
                            comentario TEXT,
                            fecha datetime NOT NULL
                            );
CREATE TABLE precios (
                            id_precio INTEGER PRIMARY KEY,
                            id_juego INTEGER NOT NULL,
                            precio REAL,
                            fecha datetime NOT NULL
                            );
CREATE INDEX precio_fecha ON precios (
                            id_juego, fecha DESC
                            );
CREATE TABLE juegos_sugeridos (
                            id_juego_sugerido INTEGER PRIMARY KEY,
                            usuario_nom TEXT NOT NULL,
                            usuario_id TEXT NOT NULL,
                            BGG_URL TEXT NOT NULL,
                            URL TEXT NOT NULL,
                            fecha datetime NOT NULL,
                            peso REAL,
                            precio_envio REAL
                            );
CREATE TABLE usuarios (
                            id_usuario INTEGER PRIMARY KEY,
                            nombre TEXT NOT NULL,
                            id INTEGER NOT NULL,
                            fecha datetime NOT NULL,
                            accion TEXT
                            );
CREATE TABLE variables (
                            id_variable INTEGER PRIMARY KEY,
                            variable TEXT NOT NULL,
                            valor TEXT NOT NULL,
                            descripcion TEXT NOT NULL,
                            fecha datetime NOT NULL
                            );
CREATE TABLE ofertas (
                            id_oferta INTEGER PRIMARY KEY,
                            id_juego INTEGER NOT NULL,
                            precio_prom REAL NOT NULL,
                            precio_actual REAL NOT NULL,
                            fecha_inicial datetime NOT NULL,
                            activa TEXT
                            );
CREATE TABLE restock (
                            id_oferta INTEGER PRIMARY KEY,
                            id_juego INTEGER NOT NULL,
                            fecha_inicial datetime NOT NULL,
                            activa TEXT NOT NULL
                            );
CREATE TABLE alarmas_ofertas (
                            id_alarma_oferta INTEGER PRIMARY KEY,
                            id_usuario INTEGER NOT NULL,
                            tipo_alarma INTEGER NOT NULL DEFAULT 3
                            );
CREATE TABLE juegos (
                            id_juego INTEGER PRIMARY KEY,
                            BGG_id INTEGER NOT NULL,
                            nombre TEXT NOT NULL,
                            sitio TEXT NOT NULL,
                            sitio_ID TEXT NOT NULL,
                            fecha_agregado datetime NOT NULL,
                            prioridad TEXT,
                            ranking INTEGER,
                            peso REAL,
                            dependencia_leng INT,
                            precio_actual REAL,
                            fecha_actual DATETIME,
                            precio_mejor REAL,
                            fecha_mejor DATETIME,
                            precio_envio REAL
                            );
