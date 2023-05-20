#!/usr/bin/python3

import time
import os
import json
import urllib
import re

import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
import pyotp

from dotenv import load_dotenv
load_dotenv()

TWITTER_EMAIL = os.getenv('TWITTER_EMAIL')
TWITTER_PASSWORD = os.getenv('TWITTER_PASSWORD')
TWITTER_OTP = os.getenv('TWITTER_OTP')
TWITTER_USERNAME = os.getenv('TWITTER_USERNAME')

RAINDROP_TOKEN = os.getenv('RAINDROP_TOKEN')

option = Options()

option.add_argument("--disable-infobars")
option.add_argument("--disable-extensions")

# Pass the argument 1 to allow and 2 to block
option.add_experimental_option("prefs", { 
    "profile.default_content_setting_values.notifications": 1 
})

driver = webdriver.Chrome(options=option, executable_path="/usr/bin/chromedriver")
driver.get('https://www.twitter.com/i/flow/login')

done = False
while not done:
    try:
        email_elem = driver.find_element_by_css_selector("input[name*='text']")
        done = True
    except NoSuchElementException:
        time.sleep(1)

email_elem.send_keys(TWITTER_EMAIL)
email_elem.send_keys(Keys.ENTER)

done = False
while not done:
    try: 
        pass_elem = driver.find_element_by_css_selector("input[name*='password']")
        done = True
    except NoSuchElementException:
        time.sleep(1)

pass_elem.send_keys(TWITTER_PASSWORD)
pass_elem.send_keys(Keys.ENTER)

time.sleep(2)

# sometimes, twitter will ask you to verify with your username
if (len(driver.find_elements_by_css_selector("input[name*='email']")) != 0):
    un_elem = driver.find_element_by_css_selector("input[name*='email']")
    un_elem.send_keys(TWITTER_USERNAME)
    pass_elem = driver.find_element_by_css_selector("input[name*='pass']")
    pass_elem.send_keys(TWITTER_PASSWORD)
    pass_elem.send_keys(Keys.ENTER)

# time.sleep(2)

otp_elem = driver.find_element_by_css_selector("input[name*='text']")
totp = pyotp.TOTP(TWITTER_OTP)
otp_elem.send_keys(totp.now())
otp_elem.send_keys(Keys.ENTER)

time.sleep(5)

driver.get('https://twitter.com/i/bookmarks')

links = []
titles = []
texts = []

with open('twitter.txt', 'a+') as f:
    f.seek(0)
    existing_links = f.read()

# scroll to bottom of page https://stackoverflow.com/a/43299513
SCROLL_PAUSE_TIME = 5

# Get scroll height
last_height = driver.execute_script("return document.body.scrollHeight")

already_added = False
while True:
    xpath_elems = driver.find_elements_by_xpath("/html/body/div[1]/div/div/div[2]/main/div/div/div/div[1]/div/div[3]/section/div/div/div[1]/div/div/article/div/div/div[2]/div[2]/div[1]/div/div[1]/div/div/div[2]/div/div[3]/a")
    if len(xpath_elems) != 0:
        link = xpath_elems[-1].get_attribute("href")
        if link in existing_links:
            already_added = True
    
    # Scroll down to bottom
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    # Wait to load page
    time.sleep(SCROLL_PAUSE_TIME)

    i = 1
    while True:
        xpath_elems = driver.find_elements_by_xpath("/html/body/div[1]/div/div/div[2]/main/div/div/div/div[1]/div/div[3]/section/div/div/div[{}]/div/div/article/div/div/div[2]/div[2]/div[1]/div/div[1]/div/div/div[2]/div/div[3]/a".format(i))
        if len(xpath_elems) == 0:
            break
        elif len(xpath_elems) == 1:
            link = xpath_elems[0].get_attribute("href")
            if link in links or link in existing_links: # check against existing links again since the first time we only check for the last elem, so some might still slip through
                i = i + 1
                continue
            print(link)
            links.append(link)
            
            title = driver.find_element_by_xpath('/html/body/div[1]/div/div/div[2]/main/div/div/div/div[1]/div/div[3]/section/div/div/div[{}]/div/div/article/div/div/div[2]/div[2]/div[1]/div/div[1]/div/div'.format(i))
            title = title.text.replace("\n", '')
            title = title.split("·", 1)[0]
            index = title.find('@')
            title = "Tweet from " + title[:index] + ' (' + title[index:] +  ')'
            print(title)
            titles.append(title)
            
            text_elems = driver.find_elements_by_xpath('/html/body/div[1]/div/div/div[2]/main/div/div/div/div[1]/div/div[3]/section/div/div/div[{}]/div/div/article/div/div/div[2]/div[2]/div[2]/div'.format(i))
            text = ''
            if len(text_elems) != 0:
                if "Replying to" not in text_elems[0].text:
                    text = text_elems[0].text
                else:
                    # for replies
                    # save "replying to" text jic "Replying to" was a false positive
                    text = text_elems[0].text
                    text_elems = driver.find_elements_by_xpath('/html/body/div[1]/div/div/div[2]/main/div/div/div/div[1]/div/div[3]/section/div/div/div[{}]/div/div/article/div/div/div[2]/div[2]/div[3]/div'.format(i))
                    if len(text_elems) != 0:
                        text = text + '\n' + text_elems[0].text

            alt_texts = driver.find_elements_by_xpath('/html/body/div[1]/div/div/div[2]/main/div/div/div/div[1]/div/div[3]/section/div/div/div[{}]/div/div/article/div/div/div[2]/div[2]/div[3]/div/div/div/div/div/div/a/div/div[2]/div/img'.format(i))
            if len(alt_texts) != 0:
                text = text + '\n' + '\n'.join(list(map(lambda x: x.get_attribute("alt"), alt_texts)))

            texts.append(text)
        i = i + 1

    # Calculate new scroll height and compare with last scroll height
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height or already_added:
        break
    last_height = new_height


driver.close()

headers = {
    'Authorization': 'Bearer ' +  RAINDROP_TOKEN,
}

l = len(links)
print('Adding ' + str(l) + ' links!')

with open('twitter.txt', 'a+') as f:
    f.seek(0)
    for i in range(len(links)):
        f.write(links[i] + '\n')
        payload = {
            'link': links[i],
            'tags': ['twitter'],
            'excerpt': links[i] + '\n' + titles[i] + '\n' + texts[i],
            'title': titles[i]
        }
        r = requests.post('https://api.raindrop.io/rest/v1/raindrop', headers=headers, json=payload)
        print(str(i + 1) + ' out of ' + str(l) + ' links added.')
        print(r.content)
        time.sleep(1)

print(str(l) + ' links added!')