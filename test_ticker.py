import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import datetime
from bs4 import BeautifulSoup
import requests
import numpy as np

#%%


##上市
url = "https://tixre.com/guest/program/detail/goz090"

chromeOptions = webdriver.ChromeOptions()
chromeOptions.add_experimental_option('useAutomationExtension', False)

driver = webdriver.Chrome()

driver.get(url)

start_buy = driver.find_element(By.XPATH, '//*[@id="tab-0"]/div[2]/div[2]/div/div[3]/a')
start_buy.click()

#//*[@id="ticket_form"]/div/table[1]/tbody/tr/td[3]/div/select 應該是這個
//*[@id="ticket_form"]/div/table[1]/tbody/tr[1]/td[3]/div


start_buy = driver.find_element(By.XPATH, '//*[@id="ticket_form"]/div/table[1]/tbody/tr[2]/td[3]/div/select')
start_buy.send_keys(1)


ans = 24
password = driver.find_element(By.XPATH, '//*[@id="captcha"]')
password.send_keys(ans)








terms_agree = driver.find_element(By.XPATH, '//*[@id="terms_agree"]')
terms_agree.click()

check_ticket = driver.find_element(By.XPATH, '/html/body/div[3]/div[1]/div[2]/div[4]/button[2]')
check_ticket.click()


