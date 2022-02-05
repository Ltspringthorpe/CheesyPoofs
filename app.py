from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import presence_of_element_located
from webdriver_manager.chrome import ChromeDriverManager
from flask import Flask, render_template, redirect, url_for, request, jsonify, make_response, Markup
from flask_cors import CORS, cross_origin
import time
import sys
import re

app = Flask(__name__)
CORS(app)

def favs():

    realm_1 = request.args.get('realm_1', '')
    toon_1 = request.args.get('toon_1')
    realm_2 = request.args.get('realm_2')
    toon_2 = request.args.get('toon_2')

    if not realm_1 or not realm_2 or not toon_1 or not toon_2:
        return '<div style="color: white;"><strong>ERROR:</strong> Missing Parameters</div>'

    a_url = 'https://worldofwarcraft.com/en-us/character/us/' + realm_1 + '/' + toon_1 + '/collections/mounts'
    b_url = 'https://worldofwarcraft.com/en-us/character/us/' + realm_2 + '/' + toon_2 + '/collections/mounts'

    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    web_driver = webdriver.Chrome(ChromeDriverManager().install())

    # store mounts, class/race specific mounts, etc
    exclude_mounts = [
        'Acherus Deathcharger',
        'Ban-Lu, Grandmaster\'s Companion',
        'Deathlord\'s Vilebrood Vanquisher',
        'Dreadsteed',
        'Farseer\'s Raging Tempest',
        'Felsteed',
        'Mystic Runesaber',
        'Netherlord\'s Accursed Wrathsteed',
        'Netherlord\'s Brimstone Wrathsteed',
        'Netherlord\'s Chaotic Wrathsteed',
        'Obsidian Nightwing',
        'Swift Windsteed',
        'The Dreadwake',
        'Winged Steed of the Ebon Blade',
        'X-53 Touring Rocket',
        'Sapphire Skyblazer'
        'Hogrus, Swine of Good Fortune',
        'Sylverian Dreamer',
        'Winged Guardian',
        'Celestial Steed',
        'Enchanted Fey Dragon',
        'Grinning Reaver',
        'Heart of the Aspects',
        'Illidari Felstalker',
        'Imperial Quilen',
        'Iron Skyreaver',
        'Lucky Yun',
        'Luminous Starseeker',
        'Mystic Runesaber',
        'Seabraid Stallion and Gilded Ravasaur',
        'Shu-Zen, the Divine Sentinel',
        'Squeakers, the Trickster',
        'Steamscale Incinerator',
        'The Dreadwake',
        'Vulpine Familiar',
        'Warforged Nightmare'
    ]

    with web_driver as driver:
        wait = WebDriverWait(driver, 2)
        a_mounts = get_mounts(a_url, driver)

        wait = WebDriverWait(driver, 2)
        b_mounts = get_mounts(b_url, driver)

        # must close the driver after task finished
        driver.close()
        driver.quit()

    a_favs = []
    for a_mount in a_mounts:
        dup = False;
        if a_mount in exclude_mounts:
            continue

        for b_mount in b_mounts:
            if a_mount == b_mount:
                dup = True;

        if not dup:
            a_favs.append(a_mount);

    b_favs = []
    for b_mount in b_mounts:
        dup = False;
        if b_mount in exclude_mounts:
            continue

        for a_mount in a_mounts:
            if b_mount == a_mount:
                dup = True;

        if not dup:
            b_favs.append(b_mount);


    a_list = '<ol style="color: white;">'
    for a_fav in a_favs:
        a_list += '<li>' + a_fav + '</li>'
    a_list += '</ol>'

    b_list = '<ol style="color: white;">'
    for b_fav in b_favs:
        b_list += '<li>' + b_fav + '</li>'
    b_list += '</ol>'

    mounts = '<div style="float: left; width: 50%;"><h4 style="color: white;">' + toon_1.capitalize() + '\'s Cheesy Poofs</h4>'
    mounts += a_list + '</div>'

    mounts += '<div style="float: left; width: 50%;"><h4 style="color: white;">' + toon_2.capitalize() + '\'s Cheesy Poofs</h4>'
    mounts += b_list + '</div>'

    return mounts

def get_mounts(url, driver):
    array = []

    # Set timeout time
    wait = WebDriverWait(driver, 5)

    # retrive url in headless browser
    driver.get(url)

    # switch tabs to Collected
    collected = driver.find_element_by_xpath('//*[@id="character-profile-mount"]/div/div/div[2]/div/div[2]/div[2]/div/div[2]/div[1]/div/div/div/button[2]/div').click()
    wait = WebDriverWait(driver, 2)

    # run the scraper
    array = scrape(array, driver)

    return array

def scrape(array, driver):
    soup = BeautifulSoup(driver.page_source, 'lxml')

    results = soup.findAll('div', class_='Pet-info-basic')
    for mount in results:
        array.append(re.sub('<.*?>', '', str(mount)))

    # find next button
    next = driver.find_element_by_class_name('Button--next')
    if next and next.is_enabled():
        next.click()
        wait = WebDriverWait(driver, 3)
        return scrape(array, driver)

    return array


@app.route('/')
def home():
    mounts = Markup(favs())
    return render_template('selenium.html', mounts=mounts)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)
