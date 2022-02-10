"""
Generar un archivo csv con todos los juegos disponibles en la pagina ludonauta.es con sus correspondientes url
para usar dicha informacion en el archivo obtener_precio.py
"""
import re
import urllib.request
from urllib.error import URLError, HTTPError


class LudonautaGetUrls:
    """Clase para extraer nombres y urls de los juegos de mesa disponibles en ludonauta.es"""
    def __init__(self):
        self.gamelist_url = "https://www.ludonauta.es/juegos-mesas/listar"
        self.total_pages = self.get_total_numb_pages()
        self.game_urls = {}

    @staticmethod
    def get_page(url: str) -> str:
        """Devuelve la respuesta del url pasado como parametro, en formato string."""
        request = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0'}
        )
        try:
            data = urllib.request.urlopen(request)
        except (HTTPError, URLError):
            return "Error"

        encoding = 'utf-8' if data.headers.get_content_charset() is None else data.headers.get_content_charset()
        try:
            page = data.read().decode(encoding, errors='ignore')
        except:
            return "Error"
        else:
            return page

    def get_total_numb_pages(self) -> int:
        """Devuelve el numero total de paginas de la lista de juegos."""
        print("Getting the number of pages to scrape")
        response = self.get_page(self.gamelist_url)
        last_page = int(re.findall(r'page:(.{1,3}?)" title="Ir a la última', response)[0])
        return last_page

    def fetch_data(self) -> None:
        """Itera entre las distintas paginas de ludonauta para extraer la informacion de los juegos."""
        print("Fetching data...")
        for index in range(1, self.total_pages + 1):
            text = self.get_page(f"https://www.ludonauta.es/juegos-mesas/listar/page:{index}")

            names = re.findall(r'class="product-name">(.*?)</a></h3>', text)
            links = re.findall(r'<h3><a href="(.*?)" ', text)
            links = ["https://www.ludonauta.es" + item for item in links]

            self.game_urls.update({name: link for name, link in zip(names, links)})
            print(f"Page [{index}]/[{self.total_pages}] done.")
        print(f"A total of {len(self.game_urls)} games have been fetched.")

    def create_csv(self) -> None:
        """Genera un archivo csv a partir de los datos obtenidos."""
        with open('../ludonauta_games_url.csv', 'w') as file:
            for name, url in self.game_urls.items():
                file.write(f"{name},{url}\n")
        print("csv file created")


if __name__ == "__main__":
    ludonauta_handler = LudonautaGetUrls()
    ludonauta_handler.fetch_data()
    ludonauta_handler.create_csv()







