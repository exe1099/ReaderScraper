import json
import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup
import os

os.chdir("/home/exe/Cloud/Informatik/Python/ReaderScraper")


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
    """Save the current cookies from browser in a text file (netscape format).

    - browser: browser instance
    """

    cookies = browser.get_cookies()
    # adding line for each cookie (netscape format)
    with open('cookies.txt', 'w') as file:
        for cookie in cookies:
            cookie_string = f"{cookie['domain']}\t" \
                         f"{cookie['http_only']}\t" \
                         f"{cookie['path']}\t" \
                         f"{cookie['secure']}\t" \
                         f"{cookie['expiry']}\t" \
                         f"{cookie['name']}\t" \
                         f"{cookie['value']}\n"
            # writing string to file
            file.write(cookie_string)
    return True


if __name__ == '__main__':
    browser = start_browser(False)
    login_reader(browser)
    save_cookie(browser)
