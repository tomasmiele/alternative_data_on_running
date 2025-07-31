import pandas as pd
import os
from openpyxl import Workbook, load_workbook
from openpyxl.utils import get_column_letter

from scraper import start_browser, get_on_reviews

if __name__ == "__main__":
    data = {}
    companies = ["On", "Hoka", "Nike", "Adidas", "New Balance"]

    for company in companies:
        data[company] = {"M": {}, "F": {}}

    driver = start_browser()
    data["On"]["M"] = get_on_reviews(driver, "m")
    data["On"]["F"] = get_on_reviews(driver, "f")
    print(data)
    driver.quit()