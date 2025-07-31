import pandas as pd
import os
from openpyxl import Workbook, load_workbook
from openpyxl.utils import get_column_letter

from scraper import start_browser, get_on_reviews

if __name__ == "__main__":
    data = {}

    driver = start_browser()
    data["On"] = get_on_reviews(driver)
    print(data)
    driver.quit()