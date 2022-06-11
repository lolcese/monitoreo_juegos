#!/bin/bash
d=$(date +%Y-%m-%d)
sqlite3 monitoreo_juegos.db ".timeout 100000" ".backup 'monitoreo_juegos_$d.db'"
tar cvfz monitoreo_juegos_$d.tar.gz monitoreo_juegos_$d.db monitoreo_juegos_todo.db
rclone copy monitoreo_juegos_$d.tar.gz gdrive:monitoreo_juegos_backup
rm monitoreo_juegos_$d.db
rm monitoreo_juegos_$d.tar.gz

sqlite3 << EOF
ATTACH 'monitoreo_juegos.db' as db1;
ATTACH 'monitoreo_juegos_todo.db' as db2;
INSERT INTO db2.precios SELECT * FROM db1.precios WHERE fecha < datetime("now", "-15 days", "localtime");
DELETE FROM db1.precios WHERE fecha < datetime("now", "-15 days", "localtime");
EOF

sqlite3 monitoreo_juegos.db << EOF
VACUUM;
EOF