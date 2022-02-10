"""
Obtener mejor precio de España.

Codigo interactivo donde se puede ver el mejor precio de un juego de mesa en España. EL usuario introduce por consola
el nombre de un juego, y se busca el menor precio de ese juego en la pagina ludonauta.es
"""
import csv
from genera_url_csv import LudonautaGetUrls
from rapidfuzz import process
import re
from typing import Optional

# Load csv
with open('ludonauta_games_url.csv', 'r') as file:
    data = csv.reader(file)
    game_urls = {row[0]: row[1] for row in data}


def get_low_price(game_name: str) -> Optional[float]:
    """Busca y devuelve el precio del juego pasado como parametro."""
    text = LudonautaGetUrls.get_page(game_urls[game_name])
    price = re.findall(r'"lowPrice": "(.{1,8}?)",', text)
    try:
        return float(price[0])
    except IndexError:
        print("Hubo un error, intentelo nuevamente.")
        return None


if __name__ == '__main__':
    while True:
        game_name_raw = input('Ingrese el nombre del juego ("q" para salir): ')
        if game_name_raw == 'q':
            break
        game_name_matched, *_ = process.extractOne(game_name_raw, game_urls.keys())
        print("buscando...")
        price = get_low_price(game_name_matched)
        if price is not None:
            print(f"juego: {game_name_matched} - menor precio: {price}")
