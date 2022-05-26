# Monitor de precios de juegos

[Monitor_Juegos_bot](https://t.me/monitor_juegos_bot) es un bot de telegram que monitorea precios de juegos desde diversos sitios (Buscalibre, Tiendamia, Bookdepository, 365games, Shop4es, Shop4world, Deepdiscount, Grooves.land, Planeton y Miniaturemarket) con una frecuencia de entre 15 minutos y 2 horas, dependiendo del número de alarmas del juego. No es un buscador, no sirve para juegos que no estén siendo monitoreados.

Ofrece la posibilidad de agregar alarmas para que te llegue una notificación cuando el precio **FINAL EN ARGENTINA** de un juego desede cualquier sitio (incluyendo 65% a compras en el exterior, tasa de Aduana y correo) sea menor al que le indicaste. Para borrar la alarma, andá al juego correspondiente.

Para ver la información de un juego en particular, elegí la opción *Ver un juego y poner/sacar alarmas* y escribí parte de su nombre. Ahí mismo vas a poder agregar alarmas cuando llegue a un determinado precio, o borrarla si lo querés.

Si no está el juego que te interesa, o si encontraste otro lugar donde lo venden, elegí en el menú la opción **Sugerir juego a monitorear**. Este agregado **no** es automático.

En *Ofertas y juegos en reposición* vas a ver todos los juegos que han bajado de precio más del 10% respecto a su promedio de 15 días, y los juegos que ahora están disponibles pero no lo estuvieron por más de 15 días.

Desde cualquier chat o grupo, escribí @Monitor_Juegos_bot y parte del nombre de un juego para ver la información de ese juego sin salir del chat.

Si un menú no responde, escribí nuevamente /start.

Cualquier duda, mandame un mensaje a [@Luis_Olcese](https://t.me/Luis_Olcese).

## Procesos que corren

### Cada 15 minutos

- monitoreo_juegos.py 1

### Cada 30 minutos

- monitoreo_juegos.py 2
- ofertas_reposiciones.py
- genera_csv.py

### Cada 120 minutos

- monitoreo_juegos.py 3

### Cada 1 día

- backup.sh
- baja_cotizacion.py
- actualiza_prioridades.py

### Cada 7 días

- baja_ranking.py
