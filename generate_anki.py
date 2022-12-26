import sys
import os
import random
import pathlib
import argparse
import genanki
import requests
import mimetypes
import bs4
from slugify import slugify

DECK_HIERARCHY = 'A1'+'::'

AUDIO_DIR_PATH = pathlib.Path("./audio").absolute()

if not AUDIO_DIR_PATH.exists():
    os.makedirs(AUDIO_DIR_PATH)

def download_asset(url):
    res = requests.get(url)
    res.raise_for_status()
    audio_filename = url.split("/")[-1]

    audio_path = f"{AUDIO_DIR_PATH}/{audio_filename}"

    if not pathlib.Path(audio_path).exists():
        with open(audio_path, "wb") as f:
            f.write(res.content)

    return audio_filename

def create_deck():
    parser = argparse.ArgumentParser()
    parser.add_argument('URL', nargs='*')
    args = parser.parse_args()

    if len(args.URL) == 0:
        print("Url wasn't supplied in the argument...")
        quit()
    else:
        print("Generating...")

    URL = str(args.URL[0])

    UNIQ_DECK_ID = random.randrange(1 << 30, 1 << 31)

    res = requests.get(URL)
    res.raise_for_status()
    
    soup = bs4.BeautifulSoup(res.text, features="lxml")

    title = soup.findAll("div", {"class": "lesson-nav-layout-wrapper"})[0].findAll("h1", {"class": "title"})[0]
    title = DECK_HIERARCHY + title.getText().strip('\n')

    vocab_list = soup.findAll("div", {"class": "sc-jKTccl kTniMK"})


    my_model = genanki.Model(
        UNIQ_DECK_ID,
        "Nico's Weg Flashcards",
        fields=[
        {'name': 'Question'},
        {'name': 'Answer'},
        {'name': 'Audio'}
        ],
        templates=[
        {
          'name': 'Card 1',
          'qfmt': '<div style="background-color: red;padding: 10px"><h1 style="text-align:center;margin-bottom:30px;">{{Question}}</h1></div><br><h1 style="text-align:center;">{{Audio}}</h1>',
          'afmt': '{{FrontSide}}<hr id="answer"><h1 style="text-align:center;margin-top: 30px;">{{Answer}}</h1>',
        },
        ])

    my_deck = genanki.Deck(UNIQ_DECK_ID, title)
    media_files = []

    # Parse English and German vocab
    for vocab in vocab_list:
        vocab_de = str(vocab.select('strong')[0].getText())
        vocab_en = str(vocab.select('p')[-1].getText())
        audio_url = vocab.find("source")['src']
        audio_name = download_asset(audio_url)
        media_files.append(f'audio/{audio_name}')

        my_note = genanki.Note(
            model=my_model,
            fields=[vocab_de, vocab_en, f'[sound:{audio_name}]'])

        my_deck.add_note(my_note)

    my_package = genanki.Package(my_deck)
    my_package.media_files = media_files
    my_package.write_to_file(title + '.apkg')
    print(title + ' is complete')

if __name__ == '__main__':
    create_deck()

