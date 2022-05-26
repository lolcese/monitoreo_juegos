#!/bin/bash
d=$(date +%Y-%m-%d)
sqlite3 monitoreo_juegos.db ".timeout 100000" ".backup '/home/lolcese/monitoreo_juegos/monitoreo_juegos_$d.db'"
tar cvfz /home/lolcese/monitoreo_juegos/monitoreo_juegos_$d.tar.gz /home/lolcese/monitoreo_juegos/monitoreo_juegos_$d.db /home/lolcese/monitoreo_juegos/monitoreo_juegos_todo.db
rclone copy /home/lolcese/monitoreo_juegos/monitoreo_juegos_$d.tar.gz gdrive:monitoreo_juegos_backup
rm /home/lolcese/monitoreo_juegos/monitoreo_juegos_$d.db
rm /home/lolcese/monitoreo_juegos/monitoreo_juegos_$d.tar.gz

sqlite3 << EOF
ATTACH '/home/lolcese/monitoreo_juegos/monitoreo_juegos.db' as db1;
ATTACH '/home/lolcese/monitoreo_juegos/monitoreo_juegos_todo.db' as db2;
INSERT INTO db2.precios SELECT * FROM db1.precios WHERE fecha < datetime("now", "-15 days", "localtime");
DELETE FROM db1.precios WHERE fecha < datetime("now", "-15 days", "localtime");
EOF

sqlite3 /home/lolcese/monitoreo_juegos/monitoreo_juegos.db << EOF
VACUUM;
EOF