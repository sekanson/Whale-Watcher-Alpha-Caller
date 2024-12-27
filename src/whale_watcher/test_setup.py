from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import pandas as pd
import numpy as np
from loguru import logger

def test_setup():
    logger.info("Testing imports and setup...")
    
    # Test pandas
    df = pd.DataFrame({'test': [1, 2, 3]})
    logger.info(f"Created test dataframe: \n{df}")
    
    # Test selenium setup
    options = Options()
    options.add_argument('--headless')
    try:
        driver = webdriver.Chrome(options=options)
        logger.info("Successfully initialized Chrome driver")
        driver.quit()
    except Exception as e:
        logger.error(f"Chrome driver error: {e}")

if __name__ == "__main__":
    test_setup()