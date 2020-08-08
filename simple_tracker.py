from amazon_config import(get_chrome_web_driver, get_web_driver_options, set_ignore_certificate_error, set_browser_as_icognito, NAME, CURRENCY, FILTERS, BASE_URL, DIRECTORY, CLONE_DIRECTORY)
#importing everything from the config file
import time

from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
#important

import json
from datetime import datetime

class generateReport:
    #whatever file name, pricing filter,base_link is the amazon link, curreny we passed (euros), scraped data result
    def __init__(self, file_name, filters, base_link, currency, data):
        self.data = data
        self.file_name = file_name
        self.filters = filters
        self.base_link = base_link
        self.currency = currency
        
        report = {
            'title': self.file_name,
            'data': self.get_now(),
            'best_item': self.get_best_item(),
            'currency': self.currency,
            'filters': self.filters,
            'base_link': self.base_link,
            'products': self.data
        }
        print("Creating report...")

        with open(f'{DIRECTORY}/data.json', 'w') as f:
            json.dump(report, f)

        with open(f'{CLONE_DIRECTORY}/data.json', 'w') as f:
            json.dump(report, f)
        print("Done...")

    def get_now(self):
        now = datetime.now()
        #user-friendly date
        return now.strftime("%d/%m/%Y %H:%M:%S")

    def get_best_item(self):
        try:
            #messed up jakob sorting based on price key, and obtaining the first element
            return sorted(self.data, key = lambda k: k['price'])[0]
        except Exception as e:
            print("Could'nt sort items")
            return None




class AmazonAPI:
    def __init__(self, search_term, filters, base_url, currency):
        #setting all variables up
        self.base_url = base_url
        self.search_term = search_term
        self.currency = currency
        options = get_web_driver_options()  
        set_browser_as_icognito(options)
        set_ignore_certificate_error(options)
        self.driver = get_chrome_web_driver(options)

        #the url you get when you filter by currency
        self.price_filter = f"&rh=p_36%3A{filters['min']}00-{filters['max']}00"


    def run(self):
        print("Starting script...")
        print(f'Looking for {self.search_term} products...')
        #links gotten from the method below
        links = self.get_products_links()

        if not links:
            print("No links received, Stopped script")
            return
        print(f"Got {len(links)} links to products...")
        print("Getting info about products...")
        products = self.get_products_info(links)
        print(f"Got info about {len(products)} products...")
        self.driver.quit()
        return products


    def get_products_links(self):
        self.driver.get(self.base_url)

        #getting the id of the search box
        element = self.driver.find_element_by_xpath('//*[@id="twotabsearchtextbox"]')
        
        #these two lines are an automation of us typing onto the search box and hitting enter
        element.send_keys(self.search_term) #ex: 'ps4'
        element.send_keys(Keys.ENTER)       #element refers to the search box
        time.sleep(2)

        #clear the url
        self.driver.get(f'{self.driver.current_url}{self.price_filter}')
        print(f"Our url: {self.driver.current_url}")
        time.sleep(2)

        #list of results (div parent container which contains all the items rendered)
        result_list = self.driver.find_elements_by_class_name('s-result-list')

        links = []
        try:#results - all the results links
            results = result_list[0].find_elements_by_xpath(
                "//div/span/div/div/div[2]/div[2]/div/div[1]/div/div/div[1]/h2/a")
            #we store all the href attribute values of each element in our links array, list comprehension
            links = [link.get_attribute('href') for link in results]
            return links
        except Exception as e:
            print("Didn't get any products...")
            return links      


    def get_products_info(self, links):
        #list of the /dp/product id, links
        asins = self.get_asins(links)
        products = []
        for asin in asins:
            product = self.get_single_product_info(asin)
            if product:
                products.append(product)
        return products


    #these 2 functions get the link and slice off the unnecessary part, in amazon theres an unnecessary
    #ref section appended to the link to track, we wanna remove it
    def get_asins(self, links):
        return [self.get_asin(link) for link in links]
    def get_asin(self, product_link):   #/dp/all the way till ref(product id)
        return product_link[product_link.find('/dp/') + 4:product_link.find('/ref')]


    def get_single_product_info(self, asin):
        print(f"Product ID: {asin} - getting data...")
        product_short_url = self.shorten_url(asin)
        #we using german link so this will convert into english
        self.driver.get(f'{product_short_url}?language=en_GB')
        time.sleep(2)

        title = self.get_title()
        seller = self.get_seller()
        price = self.get_price()
        image = self.get_image()
        rating = self.get_rating()

        #info about each inidividual product
        if title and seller and price and image and rating:
            product_info = {
                'asin:': asin,
                'url': product_short_url,
                'title': title,
                'seller': seller,
                'price': price,
                'image': image,
                'rating': rating
            }
            return product_info
        return None


    #rating of product
    def get_rating(self):
        try:
            string_value = (self.driver.find_element_by_id("acrPopover").get_attribute("title")[0])
            return float(string_value)
        except Exception as e:
            print(f"Could not get rating of product - ${self.driver.current_url}")
            return None

    #image src of the specific product
    def get_image(self):
        try:
            return self.driver.find_element_by_id('landingImage').get_attribute("src")
        except Exception as e:
            print(f"Could not get image src of product - ${self.driver.current_url}")
            return None


    #title of the specific product
    def get_title(self):
        try:
            return self.driver.find_element_by_id('productTitle').text
        except Exception as e:
            print(f"Could not get title of product - ${self.driver.current_url}")
            return None


    #seller info
    def get_seller(self):
        try:
            return self.driver.find_element_by_id('bylineInfo').text
        except Exception as e:
            print(f"Could not get seller of product - ${self.driver.current_url}")
            return None


    #price info
    def get_price(self):
        #inspecting amazon showed that there are two locations the price can be
        price = None
        try:#first location is in the price tag itself, in span tag with this id
            price = self.driver.find_element_by_id('priceblock_ourprice').text
            price = self.convert_price(price)
        #if there was no element found, run this exception
        except NoSuchElementException:
            try:#next location is this
                availability = self.driver.find_element_by_id('availability').text
                if 'Available' in availability:
                    price = self.driver.find_element_by_class_name('olp-padding-right').text
                    price = price[price.find(self.currency):]
                    price = self.convert_price(price)
            except Exception as e:
                print(f"Could not get price of a product - {self.driver.current_url}")
                return None
        #some other error, run this
        except Exception as e:
            print(f"Could not get price of a product - {self.driver.current_url}")
            return None
        return price


    #just depends on how the price is dispayed, if it has a comma n stuff we must remove it
    def convert_price(self, price):
        price = price.split(self.currency)[1]
        try:
            price = price.split("\n")[0] + "." + price.split("\n")[1]
        except:
            Exception()
        try:
            price = price.split(",")[0] + price.split(",")[1]
        except:
            Exception()
        return float(price)


    def shorten_url(self, asin):    #only amazon/product id
        return self.base_url + 'dp/' + asin #we remove the name cuz names can change, id's dont cuz cmon



if __name__ == "__main__":
    amazon = AmazonAPI(NAME, FILTERS, BASE_URL, CURRENCY)
    data = amazon.run()
    generateReport(NAME, FILTERS, BASE_URL, CURRENCY, data)