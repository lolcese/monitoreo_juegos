from datetime import datetime
import os
import psycopg2
import urllib.parse

urllib.parse.uses_netloc.append("postgres")
url = urllib.parse.urlparse(os.environ["DATABASE_URL"])

def backup_database():
    """ insert a BLOB into a table """
    conn = None
    try:
        # read data from a picture
        slqliteDBFile = open('bd/monitoreo_juegos.db', 'rb').read()
        # read database configuration
        conn = psycopg2.connect(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port
        )
        # create a new cursor object
        cur = conn.cursor()
        # execute the INSERT statement
        file_name = 'monitoreo_juegos'
        file_extension = 'db'

        cur.execute("INSERT INTO files(file_name, file_extension, fecha_backup, file_data) " +
                    "VALUES(%s, %s, %s, %s)",
                    (file_name, file_extension, datetime.now(), psycopg2.Binary(slqliteDBFile)))
        # commit the changes to the database
        conn.commit()
        # close the communication with the PostgresQL database
        cur.close()
        print("Se realizo back up de la BD!")
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()

def restore_database():
    """ read BLOB data from a table """
    conn = None
    try:
        path_to_dir = 'db/'
        # read database configuration
        conn = psycopg2.connect(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port
        )
        # create a new cursor object
        cur = conn.cursor()
        # execute the SELECT statement
        cur.execute(""" SELECT file_name, file_extension, file_data
                        FROM files order by fecha_backup desc limit 1""")

        blob = cur.fetchone()
        open(path_to_dir + blob[0] + '.' + blob[1], 'wb').write(blob[2])
        # close the communication with the PostgresQL database
        cur.close()
        print("Se recupero la bd con exito")
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()

# if __name__ == '__main__':
#     restore_database()
#     backup_database()
    