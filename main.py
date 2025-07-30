import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
from pathlib import Path
import time
from openpyxl import Workbook, load_workbook
from openpyxl.utils import get_column_letter

chrome_paths = [
    Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Users\%USERNAME%\AppData\Local\Google\Chrome\Application\chrome.exe").expanduser()
]

def find_chrome():
    for path in chrome_paths:
        if path.exists():
            return str(path)
    return None

def start_browser():
    chrome_path = find_chrome()
    if not chrome_path:
        raise FileNotFoundError("Chrome não encontrado.")
    
    options = Options()
    options.binary_location = chrome_path
    options.headless = False  
    return webdriver.Chrome(options=options)

def get_on_reviews(driver):
    on_running_men = website + "/on-running-shoes"

    wait = WebDriverWait(driver, 15)
    driver.get(on_running_men)

    try:
        accept = wait.until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler")))
        accept.click()
        print("Cookies aceitos.")
    except:
        print("Sem popup de cookies.")

    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    time.sleep(2)

    shoes = driver.find_elements(By.CSS_SELECTOR, "li.product_list.no_prices")
    data = []

    for shoe in shoes:
        try:
            name = shoe.find_element(By.CSS_SELECTOR, ".product-name a").text.strip()
        except:
            name = None
        try:
            score = shoe.find_element(By.CSS_SELECTOR, ".corescore-big__score").text.strip()
        except:
            score = None
        try:
            adjective = shoe.find_element(By.CSS_SELECTOR, ".corescore-big__text").text.strip()
        except:
            adjective = None

        data.append({
            "Name": name,
            "Score": score,
            "Adjective": adjective
        })

    return data

if __name__ == "__main__":
    website = "https://runrepeat.com/catalog"

    driver = start_browser()
    data = get_on_reviews(driver)
    print(data)
    driver.quit()