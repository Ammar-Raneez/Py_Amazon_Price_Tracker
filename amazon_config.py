from selenium import webdriver

DIRECTORY = 'reports'
CLONE_DIRECTORY = '../amazon-clone/src'
NAME = 'Laptop'
CURRENCY = '€'
MIN_PRICE = '275'
MAX_PRICE = '650'
FILTERS = {
    'min': MIN_PRICE,
    'max': MAX_PRICE
}
BASE_URL = "http://www.amazon.de/"

#gets our actual webdriver, returns webdriver of chrome
def get_chrome_web_driver(options):
    return webdriver.Chrome('./chromedriver.exe', chrome_options=options)

#again, for our options
def get_web_driver_options():
    return webdriver.ChromeOptions()

#run browser in incognito mode, ignoring certificate errors
def set_ignore_certificate_error(options):
    options.add_argument('--ignore-certificate-errors')
def set_browser_as_icognito(options):
    options.add_argument('--incognito')
