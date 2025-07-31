from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pathlib import Path
import time

website = "https://runrepeat.com/catalog"

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
            link_element = shoe.find_element(By.CSS_SELECTOR, ".product-name a")
            name = link_element.text.strip()
            relative_link = link_element.get_attribute("href")
        except:
            name = None
            relative_link = None

        try:
            score = shoe.find_element(By.CSS_SELECTOR, ".corescore-big__score").text.strip()
        except:
            score = None
        try:
            adjective = shoe.find_element(By.CSS_SELECTOR, ".corescore-big__text").text.strip()
        except:
            adjective = None

        pros, cons = [], []

        if relative_link:
            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[1])
            driver.get(relative_link)
            time.sleep(1)

            try:
                pros_elements = driver.find_elements(By.CSS_SELECTOR, "#the_good li")
                pros = [p.text.strip() for p in pros_elements if p.text.strip()]
            except:
                pros = []

            try:
                cons_elements = driver.find_elements(By.CSS_SELECTOR, "#the_bad li")
                cons = [c.text.strip() for c in cons_elements if c.text.strip()]
            except:
                cons = []

            driver.close()
            driver.switch_to.window(driver.window_handles[0])

        data.append({
            "Name": name,
            "Score": score,
            "Adjective": adjective,
            "Pros": pros,
            "Cons": cons
        })

    return data