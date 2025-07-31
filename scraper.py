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

def apply_filters_and_update_data(driver, data):
    wait = WebDriverWait(driver, 10)

    filters = {
        "Terrain": ["Road", "Trail"],
        "Pace": ["Daily running / easy", "Tempo / speed", "Competition / race"],
        "ReleaseYear": ["New", "2024", "2023", "2022", "2021 or older"]
    }

    name_to_entry = {
        entry["Name"]: {
            **entry,
            "Terrain": entry.get("Terrain", []),
            "Pace": entry.get("Pace", []),
            "ReleaseYear": entry.get("ReleaseYear", [])
        }
        for entry in data
    }

    for category, labels in filters.items():
        for label in labels:
            print(f"Aplicando filtro {label} ({category})...")

            try:
                checkbox_label = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, f"//span[contains(@class, 'checkbox-label-text') and normalize-space()='{label}']")))
                driver.execute_script("arguments[0].click();", checkbox_label)
                time.sleep(2)
            except Exception as e:
                print(f"Erro ao aplicar filtro {label}: {e}")
                continue

            while True:
                time.sleep(1)
                shoes = driver.find_elements(By.CSS_SELECTOR, "li.product_list.no_prices")

                for shoe in shoes:
                    try:
                        name = shoe.find_element(By.CSS_SELECTOR, ".product-name a").text.strip()
                        if name in name_to_entry:
                            if label not in name_to_entry[name][category]:
                                name_to_entry[name][category].append(label)
                    except Exception:
                        continue

                try:
                    next_button = driver.find_element(By.CSS_SELECTOR, "a.paginate-buttons.next-button")
                    next_url = next_button.get_attribute("href")
                    if next_url:
                        driver.get(next_url)
                        print("Indo para próxima página com filtro aplicado...")
                        time.sleep(2)
                    else:
                        break
                except:
                    break

            try:
                checkbox_label = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, f"//span[contains(@class, 'checkbox-label-text') and normalize-space()='{label}']")))
                driver.execute_script("arguments[0].click();", checkbox_label)
                time.sleep(1)
            except:
                pass

    return list(name_to_entry.values())

def get_reviews(driver, brand, gender):
    on_running_men = website + f"/{brand}-running-shoes"

    wait = WebDriverWait(driver, 15)
    driver.get(on_running_men)

    try:
        accept = wait.until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler")))
        accept.click()
        print("Cookies aceitos.")
    except:
        print("Sem popup de cookies.")

    if gender == "f":
        try:
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)

            # Seleciona o segundo botão dentro da seleção de gênero
            gender_buttons = driver.find_elements(By.CSS_SELECTOR, ".gender-select-radio a.gender-select-radio__option")
            if len(gender_buttons) >= 2:
                women_button = gender_buttons[1]
                driver.execute_script("arguments[0].click();", women_button)
                time.sleep(2)
                print("Filtro de gênero: Women aplicado.")
            else:
                print("Botões de gênero não encontrados.")
        except Exception as e:
            print("Erro ao aplicar filtro feminino:", e)
    else:
        print("Filtro de gênero: Men (default) aplicado.")

    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    time.sleep(2)

    data = []

    while True:
        time.sleep(2)

        shoes = driver.find_elements(By.CSS_SELECTOR, "li.product_list.no_prices")

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
                "Cons": cons,
                "Terrain": [],
                "Pace": [],
                "ReleaseYear": []
            })

        try:
            next_button = driver.find_element(By.CSS_SELECTOR, "a.paginate-buttons.next-button")
            next_url = next_button.get_attribute("href")
            if next_url:
                driver.get(next_url)
                print("Indo para próxima página...")
                time.sleep(2)
            else:
                print("Botão de próxima página não tem href. Encerrando.")
                break
        except:
            print("Botão de próxima página não encontrado. Encerrando.")
            break

    data = apply_filters_and_update_data(driver, data)

    return data