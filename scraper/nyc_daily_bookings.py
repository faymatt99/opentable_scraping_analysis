from selenium import webdriver
from bs4 import BeautifulSoup as soup
import re
import time
import csv
import datetime


def bookings_today(borough):
    """
    bookings_today(): given borough, visits current OpenTable search results page for that borough and extracts the number
    of bookings today for every restaurant
    
    args:
        borough: string, 'manhattan', 'bronx', 'queens', 'staten_island', or 'brooklyn'
    
    output:
        csv file named 'bookings_<borough>_<date>', where date format is 'YYYY-mm-dd'
        column headers are 'url' and <date>
    
    
    """
    
    today = datetime.datetime.today().strftime('%Y-%m-%d')
    tomorrow = (datetime.datetime.today()+datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    
    # dict of string to 'regionId' identifier number to be used in OpenTable search results url
    boroughs = {'manhattan':'16', 'bronx':'324', 'queens':'17', 'staten_island':'18', 'brooklyn':'24'}
    
    sel_borough = boroughs[borough]
    
    url = f'https://www.opentable.com/s?dateTime={tomorrow}T22%3A00%3A00&covers=1&metroId=8&regionIds%5B0%5D={sel_borough}&neighborhoodIds%5B0%5D=&term=&page=1'
    driver=webdriver.Chrome()
    driver.get(url)
    html = driver.page_source
    time.sleep(0.1)
    driver.close()
    
    # calculates how many pages of search results there are
    results_soup = soup(html, 'html.parser')
    total_restaurants = int(re.search('\d+', results_soup.find('h3', attrs = {"class" : "_6X5n-Vu8eAbxx_nrEuxjc", "data-test" : "multi-search-total-count"}).string).group(0))
    if total_restaurants % 100 == 0:
        num_results_pages = (total_restaurants/100)
    else:
        num_results_pages = int((total_restaurants/100) + 1)
    
    print(num_results_pages, ' pages of results')
    bookings_list = []
    
    # visits each search results page 
    for i in range(0, int(num_results_pages)):
        page_i = f'https://www.opentable.com/s?dateTime={tomorrow}T22%3A00%3A00&covers=1&metroId=8&regionIds%5B0%5D={sel_borough}&neighborhoodIds%5B0%5D=&term=&page={i+1}'     
        driver=webdriver.Chrome()
        driver.get(page_i)
        
        # scroll down page incrementally to load restaurant elements
        y = 500
        for timer in range(0,70):
            driver.execute_script("window.scrollTo(0, "+str(y)+")")
            y += 500
            time.sleep(0.05)
        page_i_html = driver.page_source
        time.sleep(0.1)
        driver.close()
        
        text = soup(page_i_html, 'html.parser')
        restaurants = text.find_all('div', attrs = {"class" : "_3uVfVbI1iLfMbszbU6KoOL"})
        
        for restaurant in restaurants:
            
            restaurant_child = restaurant.find('a', attrs = {"class":"_1e9PcCDb012hY4BcGfraQB"})
            
            # get restaurant url
            rest_url = restaurant_child.get('href')
            
            # get number of bookings per day
            booked_raw = restaurant.find_all('span', attrs = {"class": "_2VIffaVUDxw_-tEh-6XOB_ _2EluNCOTdgGq9H4SxGZwUg"})
            booked_today = 0
            if not (booked_raw is None):
                for span in booked_raw:
                    if 'Booked' in span.string:
                        booked_today = int(re.search('\d+', span.string).group(0)) 
                        
            # zip url and bookings into dict
            bookings_keys = ['url', today]
            bookings_dict = dict(zip(bookings_keys, [None]*2))
            bookings_dict['url'] = rest_url
            bookings_dict[today] = booked_today
            
            # append current restaurant dict to bookings_list
            bookings_list.append(bookings_dict)
            
        i+=1
    
    # write bookings_list to csv
    headings_list = ['url', today]
    with open(f'bookings_{borough}_{today}.csv', 'w', encoding = 'utf-8', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(headings_list)

        for item in bookings_list:
            csv_writer.writerow(item.values())