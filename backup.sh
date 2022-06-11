#!/bin/bash
d=$(date +%Y-%m-%d)
sqlite3 db/monitoreo_juegos.db ".timeout 100000" ".backup 'db/monitoreo_juegos_$d.db'"
tar cvfz db/monitoreo_juegos_$d.tar.gz monitoreo_juegos_$d.db db/monitoreo_juegos_todo.db
#rclone copy db/monitoreo_juegos_$d.tar.gz gdrive:monitoreo_juegos_backup
#rm db/monitoreo_juegos_$d.db
#rm db/monitoreo_juegos_$d.tar.gz

sqlite3 << EOF
ATTACH 'db/monitoreo_juegos.db' as db1;
ATTACH 'db/monitoreo_juegos_todo.db' as db2;
INSERT INTO db2.precios SELECT * FROM db1.precios WHERE fecha < datetime("now", "-15 days", "localtime");
DELETE FROM db1.precios WHERE fecha < datetime("now", "-15 days", "localtime");
EOF

sqlite3 db/monitoreo_juegos.db << EOF
VACUUM;
EOF