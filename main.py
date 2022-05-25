from time import sleep
from multiprocessing import Process

from monitoreo_juegos import main as main_monitoreo
from ofertas_reposiciones import main as main_ofertas_reposiciones
from genera_csv import main as main_genera_csv
from baja_cotizacion import main as main_baja_cotizacion
from actualiza_prioridades import main as main_actualiza_prioridades
from baja_ranking import main as main_baja_ranking
from bot_tg import main as main_bot_tg

def main():
    main_monitoreo(1)
    main_monitoreo(2)
    main_monitoreo(3)
    main_ofertas_reposiciones()
    main_genera_csv()
    main_baja_cotizacion()
    main_actualiza_prioridades()
    main_baja_ranking()
    main_bot_tg()


def procesos_cada_15_minutos():
    while 1:
        sleep(900)
        main_monitoreo(1)
def procesos_cada_60_minutos():
    sleep(600)
    while 1:
        sleep(3600)
        main_monitoreo(2)
        main_ofertas_reposiciones()
        main_genera_csv()
def procesos_cada_120_minutos():
    sleep(1200)
    while 1:
        sleep(7200)
        main_monitoreo(3)
def procesos_una_vez_por_dia():
    sleep(1800)
    while 1:
        sleep(86400)
        main_baja_cotizacion()
        main_actualiza_prioridades()
def procesos_una_vez_por_semana():
    sleep(2400)
    while 1:
        sleep(604800)
        main_baja_ranking()
def bot():
    while 1:
        main_bot_tg()


if __name__ == '__main__':
    p1 = Process(target=procesos_cada_15_minutos).start()
    p2 = Process(target=procesos_cada_60_minutos).start()
    p1 = Process(target=procesos_cada_120_minutos).start()
    p2 = Process(target=procesos_una_vez_por_dia).start()
    p1 = Process(target=procesos_una_vez_por_semana).start()
    p2 = Process(target=bot).start()
    # main()