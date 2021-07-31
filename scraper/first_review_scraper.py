from selenium import webdriver
import re
import time
import csv
import pandas as pd
import numpy as np
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import datetime

def get_earliest_review(url):
    """
    get_earliest_review: visits a restaurant page on OpenTable, scrolls to the last page of reviews, finds the
    first review ever made at that restaurant, and extracts the date that review was made
    
    args:
        url: string, the url of the restaurant page from which to extract the earliest review
        
    output:
        first review: string, 'Dined/Reviewed on <date>' or 'No Reviews' if no reviews
    
    WARNING: has bugs, ~5% of the time takes the last review on the first review page depending on how long the
    page takes to load. Adding the WebDriverWait blocks improved but did not fully solve the problem.
    
    Best used on urls taken from OpenTable search results page sorted by Newest, so that earliest reviews should be in 
    chronological order and you can identify ones where it has not navigated the reviews correctly
    """
    driver=webdriver.Chrome()
    driver.get(url)
    driver.maximize_window() # maximize to make sure page sidebar is loaded
    
    first_review = None
    
    reviews = True
    
    delay = 5
    
    # try to find the reviews element on the restaurant page for 5 seconds
    try:
        WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.XPATH, '//*[@id="reviews-results"]')))
    except:
        print("couldn't find reviews on page")
        reviews = False
        
    # if reviews found, try to find the element corresponding to the list of reviews pages
    # if reviews found to have more than 1 page, click button corresponding to final review page
    # after clicking, or if no review pagination found, get earliest review currently loaded on page
    if reviews:
        try:
            WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.XPATH, '//*[@id="review-feed-pagination"]')))
            driver.find_element_by_xpath('//*[@id="review-feed-pagination"]/div/button[last()]').click()
            try:
                WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.XPATH, '//*[@id="reviews-results"]/div[last()]/div/div[2]/div[1]/div[1]/div[2]/span')))
                time.sleep(5)
                first_review = driver.find_element_by_xpath('//*[@id="reviews-results"]/div[last()]/div/div[2]/div[1]/div[1]/div[2]/span').get_attribute('innerHTML')
            except:
                print("couldnt find final review on page")
                
        except:
            print("couldnt find button on page")
            first_review = driver.find_element_by_xpath('//*[@id="reviews-results"]/div[last()]/div/div[2]/div[1]/div[1]/div[2]/span').get_attribute('innerHTML')
    else:
        first_review = 'No reviews' # if entire reviews element missing, first review = 'No reviews'
    
    driver.close()
    return first_review