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

    toon_1 = request.args.get('toon_1', '').strip().lower()
    realm_1 = request.args.get('realm_1', '').strip().lower()
    toon_2 = request.args.get('toon_2', '').strip().lower()
    realm_2 = request.args.get('realm_2', '').strip().lower()

    if not realm_1 or not realm_2 or not toon_1 or not toon_2:
        return """<div>Input Parameters</div><br/>
            <form id="inputParams">
                <div>Character 1:</div>
                <label>Name*&nbsp;&nbsp;</label>
                <input id="toon1" type="text" name="toon_1" value=\"""" + toon_1 + """\" /><br>
                <label>Realm*&nbsp;</label>
                <input id="realm1" type="text" name="realm_1" value=\"""" + realm_1 + """\" /><br>
                <br>
                <br>
                <div>Character 2:</div>
                <label>Name*&nbsp;&nbsp;</label>
                <input id="toon2" type="text" name="toon_2" value=\"""" + toon_2 + """\" /><br>
                <label>Realm*&nbsp;</label>
                <input id="realm2" type="text" name="realm_2" value=\"""" + realm_2 + """\" /><br>
                <br>
                <br>
                <input type="submit" value="GO!" style="width: 100px;" />
            </form>"""

    a_url = 'https://worldofwarcraft.com/en-us/character/us/' + realm_1 + '/' + toon_1 + '/collections/mounts'
    b_url = 'https://worldofwarcraft.com/en-us/character/us/' + realm_2 + '/' + toon_2 + '/collections/mounts'

    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-dev-shm-usage')

    # FOR RUNNING ON PYTHON ANYWHERE -
    # web_driver = webdriver.Chrome(options=chrome_options)

    # FOR RUNNING LOCALLY -
    web_driver = webdriver.Chrome(ChromeDriverManager().install())

    # store mounts, class/race specific mounts, etc
    exclude_mounts = [
        'Acherus Deathcharger', #death knight
        'Alabaster Stormtalon', #store
        'Alabaster Thunderwing', #store
        'Armored Bloodwing', #store
        'Ban-Lu, Grandmaster\'s Companion', #monk
        'Celestial Steed', #store
        'Charger', #paladin
        'Creeping Carpet', #tailoring
        'Deathlord\'s Vilebrood Vanquisher', #death knight
        'Dreadsteed', #warlock
        'Enchanted Fey Dragon', #store
        'Ensorcelled Everwyrm', #collector's edition
        'Farseer\'s Raging Tempest', #shaman
        'Felsaber', #demon hunter
        'Felsteed', #warlock
        'Flying Carpet', #tailoring
        'Frosty Flying Carpet', #tailoring
        'Gilded Ravasaur', #collector's edition
        'Grinning Reaver', #store
        'Heart of the Aspects', #store
        'Hogrus, Swine of Good Fortune', #store
        'Illidari Felstalker', #collector's edition
        'Imperial Quilen', #collector's edition
        'Iron Skyreaver', #store
        'Lucky Yun', #store
        'Luminous Starseeker', #store
        'Magnificent Flying Carpet', #tailoring
        'Mystic Runesaber', #store
        'Netherlord\'s Accursed Wrathsteed', #warlock
        'Netherlord\'s Brimstone Wrathsteed', #warlock
        'Netherlord\'s Chaotic Wrathsteed', #warlock
        'Obsidian Nightwing', #recruit-a-friend
        'Sapphire Skyblazer', #promotion
        'Seabraid Stallion', #collector's edition
        'Shu-Zen, the Divine Sentinel', #store
        'Squeakers, the Trickster', #store
        'Steamscale Incinerator', #store
        'Swift Windsteed', #store
        'Sylverian Dreamer', #store
        'The Dreadwake', #store
        'Vulpine Familiar', #store
        'Warforged Nightmare', #store
        'Warhorse', #paladin
        'Wen Lo, the River\'s Edge', #store
        'Winged Guardian', #store
        'Winged Steed of the Ebon Blade', #death knight
        'X-53 Touring Rocket' #recruit-a-friend
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


    a_list = '<ol>'
    for a_fav in a_favs:
        a_list += '<li>' + a_fav + '</li>'
    a_list += '</ol>'

    b_list = '<ol>'
    for b_fav in b_favs:
        b_list += '<li>' + b_fav + '</li>'
    b_list += '</ol>'

    mounts = '<table><thead><tr>'
    mounts += '<th>' + toon_1.capitalize() + '\'s Cheesy Poofs</th>'
    mounts += '<th>' + toon_2.capitalize() + '\'s Cheesy Poofs</th>'
    mounts += '</tr></thead><tbody><tr>'
    mounts += '<td style="vertical-align: top;">' + a_list + '</td>'
    mounts += '<td style="vertical-align: top;">' + b_list + '</td>'
    mounts += '</tr></tbody></table>'

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
