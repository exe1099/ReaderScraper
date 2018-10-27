import json
import os
import shutil

import requests
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options


def start_browser(headless=True):
    """Starts browser.

    - headless [bool]
    - returns: browser instance
    """

    options = Options()
    # add headless option if needed
    if headless:
        options.add_argument('--headless')
    # generate path to gecko driver
    geckodriver_dir = os.path.join(os.getcwd(), 'geckodriver')
    browser = webdriver.Firefox(executable_path=geckodriver_dir, options=options)
    return browser


def login_reader(browser):
    """Login to reader.uni-mainz.de.

    - browser: browser instance which should be controlled
    - returns: True/False
    """

    # importing credentials
    login_data = json.load(open('credentials/credentials.json'))
    # open login page
    browser.get("http://reader.uni-mainz.de")
    # identifying  input fields
    username_field = browser.find_element_by_id("userNameInput")
    password_field = browser.find_element_by_id("passwordInput")
    submit_button = browser.find_element_by_id("submitButton")
    # filling input fields
    username_field.send_keys(f"UNI-MAINZ\{login_data['username']}")
    password_field.send_keys(login_data["password"])
    # submitting inputs
    submit_button.click()
    # checking login, need sleep or it won't work
    time.sleep(2)
    # check if login worked
    after_login_html = str.lower(browser.page_source)
    return str.lower(login_data["first_name"]) in after_login_html \
           and str.lower(login_data["last_name"]) in after_login_html


def save_cookie(browser):
    """Save the current cookies from browser in a text file (netscape format) in current directory.

    - browser: browser instance
    - returns: path of file
    """

    cookies = browser.get_cookies()
    for cookie in cookies:
        print(cookie)
    # adding line for each cookie (netscape format)
    with open('cookies.txt', 'w') as file:
        for cookie in cookies:
            cookie_string = f"{cookie['domain']}\t" \
                            f"{cookie['httpOnly']}\t" \
                            f"{cookie['path']}\t" \
                            f"{cookie['secure']}\t" \
                            f"{cookie['expiry']}\t" \
                            f"{cookie['name']}\t" \
                            f"{cookie['value']}\n"
            # writing string to file
            file.write(cookie_string)
    return os.path.join(os.getcwd(), 'cookies.txt')


def get_cookie_value(browser, name):
    """Returns value of cookie EdgeAccessCookie.

    - browser: browser instance
    - returns [str]: value of cookie with name EdgeAccessCookie
    """

    cookies = browser.get_cookies()
    for cookie in cookies:
        if cookie['name'] == name:
            return cookie['value']
    raise Exception(f"No cookie with name {name} found.")


def get_links_from_site_moodle(browser, url):
    """Get main links and filenames from <url> moodle.

    - browser: browser instance
    - url [str]: website
    - returns: [main links on website], [filenames]
    """

    browser.get(url)
    # can't grab links instantly
    time.sleep(3)
    inner_html = browser.page_source
    soup = BeautifulSoup(inner_html, "html5lib")
    # finding elements with links
    # element('a') == element.find_all('a')
    elements = soup('li', {'class': 'modtype_resource'})
    links = [element('a')[0].get('href') for element in elements]
    filenames = [element.get_text().lower().replace(' ', '_').replace('_file', '') + '.pdf' for element in
                 elements]
    return links, filenames


def get_links_from_site_reader(browser, url):
    """Get main links and filenames from <url> on reader.

    - browser: browser instance
    - url [str]: website
    - returns: [main links on website], [filenames]
    """

    browser.get(url)
    # can't grab links instantly
    time.sleep(3)
    inner_html = browser.page_source
    soup = BeautifulSoup(inner_html, "html5lib")
    # finding elements with links
    elements = soup.find_all('a', {'class': 'ms-listlink ms-draggable'})
    # add pre to make links absolute
    pre = "https://reader.uni-mainz.de"
    links = [pre + element.get("href") for element in elements]
    filenames = [link.split('/')[-1].lower().replace(' ', '') for link in links]
    return links, filenames


def download_links(links, filenames, directory, cookies, overwrite=False):
    """Download files from links into directory using cookies.

    - links: list of links to download
    - directory [str]: dir at which to save files, must already be created
    - cookies [dic]
    - returns: True if everything downloaded
    """

    if len(links) != len(filenames):
        raise Exception('Number of links not equal number of filenames.')

    for link, filename in zip(links, filenames):
        path = os.path.join(directory, filename)
        # don't download file if it already exists
        if not overwrite and os.path.isfile(path):
            print(f"Already downloaded: {filename}")
            continue

        print(f"Downloading {filename}.")
        r = requests.get(link, stream=True, cookies=cookies)
        with open(path, "wb") as file:
            shutil.copyfileobj(r.raw, file)
        print(f"###### New file: {filename}")


def login_moodle(browser):
    """Login to moodle.uni-mainz.de.

    - browser: browser instance which should be controlled
    - returns: True/False
    """

    # importing credentials
    login_data = json.load(open('credentials/credentials.json'))
    # open login page
    browser.get("https://moodle.uni-mainz.de/")
    # identifying  input fields
    username_field = browser.find_element_by_id("login_username")
    password_field = browser.find_element_by_id("login_password")
    submit_button = browser.find_element_by_class_name("btn.btn-primary.btn-block")
    # filling input fields
    username_field.send_keys(login_data['username'])
    password_field.send_keys(login_data["password"])
    # submitting inputs
    submit_button.click()
    # checking login, need sleep or it won't work
    time.sleep(2)
    # check if login worked
    after_login_html = str.lower(browser.page_source)
    return str.lower(login_data["first_name"]) in after_login_html \
           and str.lower(login_data["last_name"]) in after_login_html


if __name__ == '__main__':

    os.chdir("/home/exe/Cloud/Informatik/Python/ReaderScraper")
    browser = start_browser(False)
    print("Browser started.")

    sites = json.load(open('sites.json'))
    # sort sites according to website
    sites_moodle = [site for site in sites if site['url'].find('moodle.uni-mainz.de') != -1]
    sites_reader = [site for site in sites if site['url'].find('reader.uni-mainz.de') != -1]

    login = login_moodle(browser)
    print(f"Login: {login}")
    cookie_name = 'MoodleSession'
    for site in sites_moodle:
        links, filenames = get_links_from_site_moodle(browser, site['url'])
        cookie = {cookie_name: get_cookie_value(browser, cookie_name)}
        download_links(links, filenames, site['dir'], cookies=cookie)
        print(f"Site done: {site['dir']} done.")

    login = login_reader(browser)
    print(f"Login: {login}")
    cookie_name = 'EdgeAccessCookie'
    for site in sites_reader:
        links, filenames = get_links_from_site_reader(browser, site['url'])
        cookie = {cookie_name: get_cookie_value(browser, cookie_name)}
        download_links(links, filenames, site['dir'], cookies=cookie)
        print(f"Site done: {site['dir']} done.")

    print('Done!')
    browser.close()
