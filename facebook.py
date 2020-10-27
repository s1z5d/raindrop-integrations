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

FB_EMAIL = os.getenv('FB_EMAIL')
FB_PASSWORD = os.getenv('FB_PASSWORD')
FB_OTP = os.getenv('FB_OTP')

RAINDROP_TOKEN = os.getenv('RAINDROP_TOKEN')

# TODO:
# - optional: save page completely somehow?

option = Options()

option.add_argument("--disable-infobars")
option.add_argument("--disable-extensions")

# Pass the argument 1 to allow and 2 to block
option.add_experimental_option("prefs", { 
    "profile.default_content_setting_values.notifications": 1 
})

driver = webdriver.Chrome(chrome_options=option)
driver.get('https://www.facebook.com')

email_elem = driver.find_element_by_id('email')
email_elem.send_keys(FB_EMAIL)

email_elem = driver.find_element_by_id('pass')
email_elem.send_keys(FB_PASSWORD)
email_elem.send_keys(Keys.ENTER)

# get OTP
otp_elem = driver.find_element_by_id('approvals_code')
totp = pyotp.TOTP(FB_OTP)
otp_elem.send_keys(totp.now())
otp_elem.send_keys(Keys.ENTER)

# save browser prompt
driver.find_element_by_xpath("//input[@value='dont_save']").click()
driver.find_element_by_id('checkpointSubmitButton').click()

driver.get('https://www.facebook.com/saved')

# get rid of notification popup
driver.find_element_by_tag_name('body').send_keys(Keys.ESCAPE)


# scroll to bottom of page https://stackoverflow.com/a/43299513
SCROLL_PAUSE_TIME = 3

# Get scroll height
last_height = driver.execute_script("return document.body.scrollHeight")

while True:
    # Scroll down to bottom
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    # Wait to load page
    time.sleep(SCROLL_PAUSE_TIME)

    # Calculate new scroll height and compare with last scroll height
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        break
    last_height = new_height

links = []
titles = []

# This bit works for links that are saved from posts
# get links 
link_elems = driver.find_elements_by_xpath("//span[contains(text(), 'Saved from')]//child::a[1]")
title_elems = driver.find_elements_by_xpath("//span[contains(text(), 'Saved from')]//child::a[1]//child::span[1]")

for le, te in zip(link_elems, title_elems):
    links.append(le.get_attribute("href"))
    titles.append(le.get_attribute("innerHTML"))

driver.close()

print(len(links), len(titles))

# add links to raindrop
headers = {
    'Authorization': 'Bearer ' +  RAINDROP_TOKEN,
}
for i in range(len(links)):    
    with open('facebook.txt', 'a+') as f:
        existing_links = f.read()
        if links[i] not in existing_links:
            f.write(links[i] + '\n')
            payload = {
                'link': links[i],
                'tags': ['facebook'],
                'excerpt': links[i],
                'title': titles[i] + ' from Facebook'
            }
            r = requests.post('https://api.raindrop.io/rest/v1/raindrop', headers=headers, json=payload)
            print(r.content)
            time.sleep(1)

# This bit works for links that don't have any posts associated with them.
# i = 1
# while True:
#     xpath_elems = driver.find_elements_by_xpath('/html/body/div[1]/div/div[1]/div[1]/div[3]/div/div/div[1]/div[1]/div[2]/div/div/div/div/div[2]/div[{}]/div/div/div/div[2]/a | /html/body/div[1]/div/div[1]/div[1]/div[3]/div/div/div[1]/div[1]/div[2]/div/div/div/div/div[2]/div[{}]/div/div/div/div[2]/div/div[2]/div/div[2]/span'.format(i, i))
#     if len(xpath_elems) == 0:
#         break
#     elif len(xpath_elems) == 1:
#         # clean link
#         link = xpath_elems[0].get_attribute("href")
#         cleaned_link = re.sub(r"\?fbclid=.*", '', urllib.parse.unquote(link.replace("https://l.facebook.com/l.php?u=", '')))
#         links.append(cleaned_link)
#         title = driver.find_element_by_xpath('/html/body/div[1]/div/div[1]/div[1]/div[3]/div/div/div[1]/div[1]/div[2]/div/div/div/div/div[2]/div[{}]/div/div/div/div[2]/a/span/span'.format(i)).get_attribute("innerHTML")
#         titles.append(title)
#     i = i + 1

# driver.close()

# print(len(links), len(titles))

# # add links to raindrop
# headers = {
#     'Authorization': 'Bearer ' +  RAINDROP_TOKEN,
# }
# for i in range(len(links)):    
#     with open('facebook.txt', 'a+') as f:
#         existing_links = f.read()
#         if links[i] not in existing_links:
#             f.write(links[i] + '\n')
#             payload = {
#                 'link': links[i],
#                 'tags': ['facebook_link'],
#                 'excerpt': links[i] + '\n' + titles[i],
#             }
#             r = requests.post('https://api.raindrop.io/rest/v1/raindrop', headers=headers, json=payload)
#             print(r.content)
#             time.sleep(1)