from selenium import webdriver
from bs4 import BeautifulSoup as soup
import re
import time
import csv

def nyc_opentable_scraper(borough, date, starting_page):
    """
    nyc_opentable_scraper: given a borough and date, scrapes the OpenTable search results front page to see how many pages of
    results there are for that borough and date. Calls get_restaurants() on each of those results pages, and writes
    the information scraped from each restaurant to a line in a csv file by calling restaurants_to_csv()
    
    args:
        borough: string, one of 'manhattan', 'brooklyn', 'bronx', 'queens', or 'staten_island'
        date: string in format 'YYYY-mm-dd'
            WARNING: passing a date earlier than the current date will not provide correct information
        starting_page: int, the number of the search results pages to start scraping from
            Usually 1. Mostly implemented to pick up where it left off during debugging if there was an error
    
    output:
        Creates a csv file named <date>_<borough>_page<i> for each page of search results for input borough and date
    
    """
    i = starting_page
    frontpages = {
    'manhattan' : f'https://www.opentable.com/s?dateTime={date}T20%3A00%3A00&covers=1&metroId=8&regionIds%5B%5D=16&term=&corrid=d0436a58-4f45-4c4f-9992-e70b98b5157f&sortBy=newest_arrivals&queryUnderstandingType=none&page={i}',
    'brooklyn' : f'https://www.opentable.com/s?dateTime={date}T20%3A00%3A00&covers=1&metroId=8&regionIds%5B%5D=24&term=&corrid=d12a66c7-6561-4119-8bd9-8ddfb2719cca&sortBy=newest_arrivals&queryUnderstandingType=none&page={i}',
    'queens' : f'https://www.opentable.com/s?dateTime={date}T20%3A00%3A00&covers=1&metroId=8&regionIds%5B%5D=17&term=&corrid=b58c0eae-160f-4ef7-90d7-c228211fe416&sortBy=newest_arrivals&queryUnderstandingType=none&page={i}',
    'bronx' : f'https://www.opentable.com/s?dateTime={date}-20T20%3A00%3A00&covers=1&metroId=8&regionIds%5B%5D=324&term=&corrid=b58c0eae-160f-4ef7-90d7-c228211fe416&sortBy=newest_arrivals&queryUnderstandingType=none&page={i}',
    'staten_island' :  f'https://www.opentable.com/s?dateTime={date}T20%3A00%3A00&covers=1&metroId=8&regionIds%5B%5D=18&term=&corrid=b58c0eae-160f-4ef7-90d7-c228211fe416&sortBy=newest_arrivals&queryUnderstandingType=none&page={i}'   
    }
    
    if borough not in frontpages:
        raise ValueError("The 5 boroughs are 'manhattan', 'brooklyn', 'bronx', 'queens', and 'staten_island'")
    
    results_frontpage = frontpages[borough]
    driver=webdriver.Chrome()
    driver.get(results_frontpage)
    frontpage_html = driver.page_source
    time.sleep(0.1)
    driver.close()
    
    frontpage_soup = soup(frontpage_html, 'html.parser')
    total_restaurants = int(re.search('\d+', frontpage_soup.find('h3', attrs = {"class" : "_6X5n-Vu8eAbxx_nrEuxjc", "data-test" : "multi-search-total-count"}).string).group(0))
    print(total_restaurants)
    if total_restaurants % 100 == 0:
        num_results_pages = (total_restaurants/100)
    else:
        num_results_pages = int((total_restaurants/100) + 1)
    
    print(f'Total results pages: {num_results_pages}')
          
    rest_keys = ['name', 'url', 'is_member', 'promoted', 'price_tier', 'review_count', 'overall', 'food', 'service', 'ambience', 'value',
       'noise', 'pct_recommended', 'neighborhood', 'cuisines', 'dining_style', 'dress_code', 'chef', 'tags',
       'primary_cuisine', 'sanitizing', 'distancing', 'ppe', 'screening']
    i = 1
    while i <= num_results_pages:
        page_i = frontpages[borough]
        print(page_i)
        page_i_rest_list = get_restaurants(page_i)
        restaurants_to_csv(page_i_rest_list, f'{date}_{borough}_page{i}.csv', rest_keys)
        print()
        print(f'exported page {i}')
     
def get_restaurants(results_url):
    """
    get_restaurants: gets names, urls, and promoted status of all restaurant pages on a given search results page
        Calls get_restaurant_info() on each of the urls found.
    
    args:
        results_url: the url of the search results page to scrape
        
    output:
        rest_list: a list of dictionaries, each containing the information from one restaurant, scraped both by
        this function and by get_restaurant_info()
    """
    driver=webdriver.Chrome()
    driver.get(results_url)

    # scroll down page incrementally to load restaurant elements
    y = 500
    for timer in range(0,70):
        driver.execute_script("window.scrollTo(0, "+str(y)+")")
        y += 500
        time.sleep(0.05)
    results_html = driver.page_source
    time.sleep(0.1)
    driver.close()
    
    
    results = soup(results_html, 'html.parser')
    restaurants = results.find_all('div', attrs = {"class" : "_3uVfVbI1iLfMbszbU6KoOL"})
    print(f'{len(restaurants)} restaurants on results page {results_url} found')
    
    rest_list = [None]*len(restaurants)
    
    rest_keys = ['name', 'url', 'is_member', 'promoted', 'price_tier', 'review_count', 'overall', 'food', 'service', 'ambience', 'value',
       'noise', 'pct_recommended', 'neighborhood', 'cuisines', 'dining_style', 'dress_code', 'chef', 'tags',
       'primary_cuisine', 'sanitizing', 'distancing', 'ppe', 'screening']
    
    i = 0
    for restaurant in restaurants:
        
        # initialize all keys to None
        curr_rest_dict = dict(zip(rest_keys, [None]*len(rest_keys)))
        
        # get restaurant name
        restaurant_child = restaurant.find('a', attrs = {"class":"_1e9PcCDb012hY4BcGfraQB"})
        curr_rest_dict['name'] = restaurant_child.get('aria-label')

        # get restaurant url
        rest_url = restaurant_child.get('href')
        curr_rest_dict['url'] = rest_url
        
        # check whether restaurant is on opentable's reservation service. If not, there will be no details on restaurant page and we can skip
        curr_rest_dict['is_member'] = 0 if restaurant.find('p', attrs = {"class":"_1RzTbFM0hmdDgWfT_RmXel"}) else 1

        if curr_rest_dict['is_member'] == 1:

            # get promoted status
            curr_rest_dict['promoted'] = 1 if restaurant.get('data-promoted') == 'true' else 0

            get_restaurant_info(curr_rest_dict['url'], curr_rest_dict)

        print(curr_rest_dict['name'], end = ', ')
        rest_list[i] = curr_rest_dict
        i+=1
         
    return rest_list

def get_restaurant_info(url, curr_rest_dict):
    """
    get_restaurant_info: extracts information from restaurant pages whose urls were found by get_restaurants()
    
    args:
        url: url of the restaurant page
        curr_rest_dict: the dict of information on each restaurant generated by get_restaurants()
    
    output:
        no return, mutating function
        navigates the restaurant page and adds the following keys and values to curr_rest_dict:
            
            review_count: int, total # of reviews received
            ----------------------------------------------------------------------------
            
            RATINGS- all rating values are floats, out of 5.0 maximum rating
            -----------------------------------------------------------------------------
            overall: overall average rating by reviewers
            food: average food rating by reviewers
            service: average service rating by reviewers
            ambience: average ambience rating by reviewers
            value: average value rating by reviewers
            -----------------------------------------------------------------------------
            
            noise: string, noise level. Quiet, Moderate, or Energetic.
            pct_recommended: int, percent of reviewers who would recommend restaurant to a friend
            -----------------------------------------------------------------------------
            
            DETAILS- all details values are strings, with None if key not found on page
            -----------------------------------------------------------------------------
            neighborhood: neighborhood in which restaurant is located
            hours: hours of operation
            cuisines: cuisine styles served
            dining_style: dining style (fine dining, casual, etc)
            dress_code: dress code
            chef: chef's name
            tags: additional tags
            primary_cuisine: first item in cuisines, as listed on results page
            -----------------------------------------------------------------------------
            
            COVID-19 MEASURES- all values are bool, 1 if safety measure is implemented, 0 if not
            -----------------------------------------------------------------------------
            sanitizing: sanitization or enhanced cleaning practices
            distancing: physical distancing, barriers between tables, etc
            ppe: (personal protective equipment) mask-wearing by staff and requiring customers to do so
            screening: customer temperature checking, contact tracing
        
    """
    driver=webdriver.Chrome()
    driver.get(url)
    driver.maximize_window() # maximize to make sure page sidebar is loaded
    rest_html = driver.page_source
    driver.close()

    curr_rest = soup(rest_html, 'html.parser')
    
    # get number of reviews, price range
    divs = curr_rest.find_all('div', attrs = {"class" : "c3981cf8 _965a91d5"})
    for div in divs:
        spans = div.find_all('span')
        for span in spans:
            if "Reviews" in span.string:
                curr_rest_dict['review_count'] = span.string
            if "$" in span.string:
                curr_rest_dict['price_tier'] = span.string
                
    has_reviews = 1 
    if curr_rest_dict['review_count'] == "No Reviews":
        has_reviews = 0
    
    # get overall rating and subratings
    if has_reviews:
        curr_rest_dict['overall'] = float(curr_rest.find('div', attrs = {"class" : "oc-reviews-491257d8"}).span.string)
        subreviews = curr_rest.find_all('div', attrs = {"class" : "oc-reviews-15d38b07"})
        if subreviews != []:
            curr_rest_dict['food'] = float(subreviews[0].string)
            curr_rest_dict['service'] = float(subreviews[1].string)
            curr_rest_dict['ambience'] = float(subreviews[2].string)
            curr_rest_dict['value'] = float(subreviews[3].string)

    # get noise level
    noise_level = curr_rest.find('span', attrs = {"class" : "oc-reviews-624ebf8b"})
    if not (noise_level is None):
        curr_rest_dict['noise'] = noise_level.string
    

    # get percent of reviewers who would recommended to a friend
    if has_reviews:
        recs_parent = curr_rest.find_all('div', attrs = {"class" : "oc-reviews-8c8e52a0"})
        has_recs = 0
        for div in recs_parent:
            spans = div.find_all('span', attrs = {"class" : "oc-reviews-624ebf8b"})
            for span in spans:
                if span.string == 'would recommend it to a friend':
                    has_recs = 1
        
        if has_recs == 1:
            recs = curr_rest.find_all('div', attrs = {"class" : "oc-reviews-dfc07aec"})[1]
            recs_2 = re.search('\d+%', recs.get_text())
            if not (recs_2 is None):
                rec_string = recs_2.group(0)
                curr_rest_dict['pct_recommended'] = int(re.search('\d+', rec_string).group(0))

    details_tags = ['neighborhood', 'cuisines', 'dining_style', 'dress_code', 'chef', 'tags']

    # zip (field, value) tuples of restaurant page sidebar information into details_list
    sidebar = curr_rest.find('div', attrs = {"class":"_1e466fbf"})
    if not(sidebar is None):
        details = sidebar.find_all('div', attrs = {"class":"df8add00"})
        details_list = [zip(item.find_all('div', attrs = {"class":"c3981cf8 _965a91d5"}), 
                            item.find_all('div', attrs = {"class":"e7ff71b6 b2f6d1a4"})) for item in details] 
        for i in range(len(details_list)):
            for x, y in details_list[i]:
                details_list[i] = (x.string, y.string)

        # filter details_list for desired information, add info to curr_rest_dict
        desired_details = zip(['Neighborhood', 'Cuisines', 'Dining Style', 'Dress code', '(?i)(.*chef.*)', 'Additional'], details_tags)

        for x, y in desired_details:
            for a, b in details_list:
                if re.search(x, a):
                    curr_rest_dict[y] = b
    
    # gets first tag in cuisines as primary cuisine
    if not (curr_rest_dict['cuisines'] is None):
        curr_rest_dict['primary_cuisine'] = curr_rest_dict['cuisines'].split(',')[0]
    
    # check whether restaurant has safety information element at all
    if not (curr_rest.find('div', attrs = {"id" : "safety-precautions"}) is None):
        
        safety_categories = ['Cleaning & Sanitizing', 'Physical Distancing', 'Protective Equipment','Screening']
        safety_tags = ['sanitizing', 'distancing', 'ppe', 'screening']
        
        # set keys for safety information to 0
        for item in safety_tags:
            curr_rest_dict[item] = 0


        # get COVID-19 safety information
        safety_html = curr_rest.find_all('div', attrs = {"class" : "_77b505d0 _965a91d5"})
        safety_features = [item.find('span').string for item in safety_html]

        for i in range(len(safety_categories)):
            for j in range(len(safety_features)):
                if safety_categories[i] == safety_features[j]:
                    curr_rest_dict[safety_tags[i]] = 1


def restaurants_to_csv(rest_list, filename, headings_list):
    """
    writes information scraped by other functions to csv file
    
    Args: 
        rest_list: the list of dictionaries of restaurant information created by get_restaurants()
        filename: string, the name of the output csv file
        headings_list: list containing column names for the csv file
        
    """
    with open(filename, 'w', encoding = 'utf-8', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(headings_list)

        for rest_dict in rest_list:
            csv_writer.writerow(rest_dict.values())