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


def get_access_code(browser):
    """Returns value of cookie EdgeAccessCookie.

    - browser: browser instance
    - returns [str]: value of cookie with name EdgeAccessCookie
    """

    cookies = browser.get_cookies()
    for cookie in cookies:
        if cookie['name'] == "EdgeAccessCookie":
            return cookie['value']
    raise Exception("No cookie with name EdgeAccessCookie found.")


def get_links_from_site(browser, url):
    """Get main links from <url>.

    - browser: browser instance
    - url [str]: website
    - returns: list of main links on website
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
    return links


def download_links(links, directory, cookies):
    """Download files from links into directory using cookies.

    - links: list of links to download
    - directory [str]: dir at which to save files, must already be created
    - cookies [dic]
    - returns: True if everything downloaded
    """

    for link in links:
        filename = link.split('/')[-1]
        path = os.path.join(directory, filename)

        print(f"Downloading {filename}.")
        r = requests.get(link, stream=True, cookies=cookies)
        with open(path, "wb") as file:
            shutil.copyfileobj(r.raw, file)
        print(f"Download finished.")


if __name__ == '__main__':

    browser = start_browser()
    print("Browser started.")

    login = login_reader(browser)
    print(f"Login: maybe {login}.")

    sites = json.load(open('sites.json'))

    for site in sites:
        links = get_links_from_site(browser, site['url'])
        cookies = {"EdgeAccessCookie": get_access_code(browser)}
        download_links(links, site['dir'], cookies)
        print(f"Site belonging to {site['dir']} done.")
    print('Done!')
    browser.close()
