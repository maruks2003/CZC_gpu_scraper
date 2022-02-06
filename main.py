from datetime import date
import requests
import bs4
import os
import csv

RETRIES = 3
MAIN_PAGE = "https://www.czc.cz"

def main():
    soup = get_soup_from_url(MAIN_PAGE+"/graficke-karty/produkty", RETRIES)
    pages = iterate_shop_pages(soup)
    gpus = {}

    for page in pages:
        gpus.update(get_graphics_card_info(get_soup_from_url(page, RETRIES)))

    log_gpus(gpus)

def log_gpus(gpus: {str:str}):
    """
    logs the gpus prizes into .csv file
    """
    filename = "gpu_price-log.csv"
    gpus["Date"] = str(date.today())

    # If we already have some data written down, save them to memory.
    # XXX: This can be a huge memory hog, so you might want to change it
    #      one day.
    contents = ""
    if os.path.isfile(filename):
        with open(filename) as f:
            contents = f.read().split('\n')

    # Turn the `original_gpus` into a dict
    original_gpus = dict()
    for line in contents:
        gpu    = line.split(';')[0]
        prices = line.split(';')[1:]
        original_gpus[gpu] = prices

    # If the `Date` column doesn't exist in the csv, add it
    if "Date" not in original_gpus:
        original_gpus["Date"] = []
    # If we already got the data today, just discard the newly scraped data.
    elif original_gpus["Date"][-1] == gpus["Date"]:
        print("Data already scraped today. Discarding...")
        return

    # Create a new empty column for each gpu
    for gpu in original_gpus.keys():
        original_gpus[gpu].append("")

    # Replace the empty space in the new columns, if we can.
    # If a GPU was removed from the store, the column for today will be left
    # empty.
    for gpu in gpus.keys():
        # If we are not yet tracking the GPU (that is, if a new one was added),
        # start tracking it and leave the previous columns empty
        if gpu not in original_gpus:
            original_gpus[gpu] = ["" for i in range(len(original_gpus["Date"]))]
        original_gpus[gpu][-1] = gpus[gpu]

    # Turn the dictionary into a csv-compliant format
    contents = ""
    for gpu in original_gpus.keys():
        if gpu != "":
            contents += "{};{}\n".format(gpu, ';'.join(original_gpus[gpu]))

    # Write the data to the filesystem
    with open(filename, "w") as f:
        f.write(contents)

def get_soup_from_url(url: str, retries: int) -> bs4.BeautifulSoup:
    """
    Gets the soup from 'url' and returns it as soup if valid, otherwise 'None'
    """
    r = requests.get(url)

    while r.status_code != 200 and retries >= 0:
        print(f"Error {r.status_code} trying again ({retries})...")
        r = requests.get(url)
        retries -= 1

    if r.status_code != 200:
        print("Couldn't fetch your mom, too big. Aborting!")
        exit(1)

    return bs4.BeautifulSoup(r.text, "html.parser")

def get_graphics_card_info(soup: bs4.BeautifulSoup) -> {str:str}:
    """
    Gets urls of the GPUs on current page and puts them in an array for later use
    """
    gpus = {}
    tiles = soup.find_all(class_="new-tile")
    for tile in tiles:
        name = tile.get("data-ga-impression").split(",\"")[2].split(":")[1].replace("\"", "")
        price = tile.get("data-ga-impression").split(",\"")[4].split(":")[1]
        gpus[name] = price
    return gpus

def iterate_shop_pages(soup: bs4.BeautifulSoup) -> [str]:
    """
    Iterates through all the pages on navigation of the current page and
    calls the function on each of them
    """

    gpu_urls = []
    incrementor = 27
    last = int(soup.find(class_="last").get("href").split("=")[-1])
    for i in range(incrementor, last+incrementor)[::incrementor]:
        gpu_urls.append(f"{MAIN_PAGE}/graficke-karty/produkty?q-first={i}")
    return gpu_urls

if __name__ == '__main__':
    main()
