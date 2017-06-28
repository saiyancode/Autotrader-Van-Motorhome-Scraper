from bs4 import BeautifulSoup
import datetime
import sqlite3 as sql
import time
from selenium import webdriver
import re

url = 'http://motorhomes.autotrader.co.uk/search?locationName=LONDON&latitude=51.4879990129&longitude=-0.1405074285&postcode=SW1V%204DA'
url = 'http://www.autotrader.co.uk/van-search?sort=sponsored-supplied&radius=1500&postcode=sw1v4da&body-type=Panel%20Van&wheelbase=LWB'

conn = sql.connect(r'Vans2.db')
c = conn.cursor()
unix = int(time.time())
date = str(datetime.datetime.fromtimestamp(unix).strftime('%Y-%m-%d'))
brands = [line.rstrip('\n') for line in open('brands.txt')]
van_brands = [line.rstrip('\n') for line in open('van_brands.txt')]

def create_table():
    c.execute("CREATE TABLE IF NOT EXISTS motordata(date TEXT, url TEXT PRIMARY KEY, title TEXT, age INTEGER, attributes TEXT, miles TEXT, price TEXT, brand TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS vandata(date TEXT, url TEXT PRIMARY KEY, title TEXT, age INTEGER, attributes TEXT, miles TEXT, price TEXT, brand TEXT)")

def type_url():
    if url.find('motorhomes.autotrader') != -1:
        type = 'motor'
    else:
        type = 'van'
    return type

def pages(soup):
    num = soup.find('span',attrs={'class':'totalPages'})
    num = num.text
    length = []
    for i in range(int(num)):
        length.append(i+1)
    return length[1:]

def pages_van(soup):
    num = soup.find('li',attrs={'class':'paginationMini__count'})
    num = num.text
    num = re.sub('Page 1 of ','',num)
    length = []
    for i in range(int(num)):
        length.append(i+1)
    return length[1:]

class data_extract():

    def __init__(self):
        print("process")

    def motor(self,driver,url):
        driver.get(url)
        soup = BeautifulSoup(driver.page_source)
        self.length = pages(soup)
        try:
            results = soup.findAll('div', attrs={'class': 'searchResult '})
            for a, b in enumerate(results):
                soup = b
                header = soup.find('h2')
                title = header.text.replace('\n', ' ').replace('\r', '')
                link = header.find('a')
                link = link['href']
                age = soup.find('div', attrs={'class': 'advertAge'})
                age = age.text.replace('\n', ' ').replace('\r', '').replace('\t', '')
                attributes = soup.find('ul', attrs={'class': 'advertSpecs'})
                attributes = attributes.text.replace('\n', ' ').replace('\r', '')
                price = soup.find('div', attrs={'class': 'advertPrice'})
                price = price.text.replace('\n', ' ').replace('\r', '').replace('\t', '')
                try:
                    miles = re.search('[0-9,]+ Miles', attributes).group()
                    miles = re.sub(r' Miles', '', miles)
                except:
                    miles = None

                for brand in brands:
                    try:
                        if re.search(brand, title).group() != None:
                            brand = brand
                            break
                    except:
                        continue

                c.execute("INSERT INTO motordata VALUES (?,?,?,?,?,?,?,?)",
                          (date, link, title, age, attributes, miles, price, brand))
                conn.commit()
        except Exception as e:
            print(e)

    def get_length_motor(self):
        return self.length

    def vans(self,driver,url):
        driver.get(url)
        soup = BeautifulSoup(driver.page_source)
        self.length_van = pages_van(soup)
        results = soup.findAll('li', attrs={'class': 'search-page__result'})
        print(len(results))
        for a, b in enumerate(results):
            soup = b
            header = soup.find('h2')
            title = header.text.replace('\n', ' ').replace('\r', '')
            # If the search result is an add then
            try:
                link = soup.find('a', attrs={'class': 'listing-fpa-link'})
                link = link['href']
                link = re.sub('\?.*', '', str(link))
            except:
                continue

            try:
                attributes = soup.find('ul', attrs={'class': 'listing-key-specs '})
                attributes = attributes.text.replace('\n', ' ').replace('\r', '')
            except:
                attributes = soup.find('ul', attrs={'class': 'listing-key-specs write-off-cat'})
                attributes = attributes.text.replace('\n', ' ').replace('\r', '')

            price = soup.find('div', attrs={'class': 'vehicle-price'})
            price = price.text.replace('\n', ' ').replace('\r', '').replace('\t', '')

            try:
                miles = re.search('[0-9,]+ miles', attributes).group()
                miles = re.sub(r' miles', '', miles).replace(' ', '').replace('\t', '')
            except:
                miles = None

            try:
                age = re.sub(r' \(.*', '', attributes).replace(' ', '').replace('\t', '')
            except:
                age = None

            for brand in van_brands:
                try:
                    if re.search(brand.lower(), title.lower()).group() != None:
                        brand = brand
                        break
                except:
                    continue

            c.execute("INSERT INTO vandata VALUES (?,?,?,?,?,?,?,?)",
                      (date, link, title, age, attributes, miles, price, brand))
            conn.commit()

    def get_length_van(self):
        return self.length_van

def ranks(url):
    url = url
    driver = webdriver.Chrome(executable_path='/Users/willcecil/Dropbox/Python/chromedriver')
    extractor = data_extract()
    extractor.motor(driver,url)
    for i in extractor.get_length_motor():
        urlnew = url + '&pageNumber=' + str(i)
        extractor.motor(driver,urlnew)
    driver.quit()

def ranks_van(url):
    url = url
    driver = webdriver.Chrome(executable_path='/Users/willcecil/Dropbox/Python/chromedriver')
    extractor = data_extract()
    extractor.vans(driver, url)
    for i in extractor.get_length_van():
        urlnew = url + '&page=' + str(i)
        extractor.vans(driver,urlnew)
    driver.quit()

if __name__ == "__main__":
    create_table()
    if type_url() == 'motor':
        ranks(url)
    else:
        ranks_van(url)
    conn.close()





