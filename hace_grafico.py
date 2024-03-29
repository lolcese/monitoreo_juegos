import sqlite3
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FormatStrFormatter
import constantes
from random import randint

def grafica(bgg_id, nombre, db):
    conn = sqlite3.connect(constantes.db_file, timeout=20, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.execute("PRAGMA journal_mode=WAL")
    cursor = conn.cursor()
    if db == "actual":
        cursor.execute('SELECT precio_mejor FROM juegos WHERE precio_mejor NOT NULL AND bgg_id = ?',[bgg_id])
        valido = cursor.fetchone()
    else: # Si son precios históricos
        conn_h = sqlite3.connect(constantes.db_file_histo, timeout=20, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        conn_h.execute("PRAGMA journal_mode=WAL")
        cursor_h = conn_h.cursor()
        valido = True

    if valido is not None: # Si hay algún dato válido
        cursor.execute('SELECT id_juego, sitio FROM juegos WHERE bgg_id = ?',[bgg_id])
        juego = cursor.fetchall()
        plt.ioff()
        hay_datos = False
        leyenda = []
        plt.rc('xtick', labelsize=8)
        fig, ax1 = plt.subplots()
        ax1.set_xlabel('Fecha')
        ax1.set_ylabel('Precio $')
        ax1.ticklabel_format(useOffset=False)
        ax1.tick_params(axis='y')
        plt.grid()
        fig.suptitle(nombre)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m/%y"))
        ax1.yaxis.set_major_formatter(FormatStrFormatter('%.0f'))
        ax1.tick_params(axis='x', labelrotation= 45)
        for i in juego:
            id_juego, sitio = i
            cursor.execute('SELECT precio, fecha as "[timestamp]" FROM precios WHERE id_juego = ? ORDER BY fecha',[id_juego])
            datos = cursor.fetchall()
            if db == "historico":
                cursor_h.execute('SELECT precio, fecha as "[timestamp]" FROM precios WHERE id_juego = ? ORDER BY fecha',[id_juego])
                datos_h = cursor_h.fetchall()
                datos = datos_h + datos
            if len(datos) > 0:
                hay_datos = True
                precio_hi = [sub[0] for sub in datos]
                fecha_hi = [sub[1] for sub in datos]
                ax1.plot(fecha_hi, precio_hi, marker='o', linestyle='dashed', markersize=5)
                leyenda.append(constantes.sitio_nom[sitio])

        if hay_datos == True:
            fig.tight_layout(rect=[0, 0.01, 1, 0.97])
            plt.legend(leyenda)
            arch = f"temp/{randint(0, 9999999999)}.png"
            plt.savefig(arch,dpi=100)
            plt.close('all')
        else:
            arch = None    

    else: # Si no hay datos válidos
        arch = None

    return arch