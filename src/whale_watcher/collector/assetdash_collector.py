import time
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
import json

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

class AssetDashCollector:
    def __init__(self):
        self.base_url = "https://swap.assetdash.com/"
        self.email = os.getenv("ASSETDASH_EMAIL")
        self.password = os.getenv("ASSETDASH_PASSWORD")
        self.driver = None
        
    def setup_driver(self):
        """Initialize Chrome WebDriver."""
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        logger.info("Chrome WebDriver initialized")
        
    def login(self) -> bool:
        """Log in to AssetDash."""
        try:
            # Navigate to page first
            logger.info("Navigating to login page...")
            self.driver.get(self.base_url)
            time.sleep(3)

            # First look for Select Wallet button - if we see this, we're not logged in
            if not self.check_login_status():
                logger.info("Not logged in, proceeding with login...")
                
                # Look for and click Log In button
                login_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Log In')]"))
                )
                login_button.click()
                logger.info("Clicked Log In button")
                time.sleep(2)

                # Fill login form
                email_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
                )
                email_field.clear()
                email_field.send_keys(self.email)
                logger.info("Email entered")

                password_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
                password_field.clear()
                password_field.send_keys(self.password)
                logger.info("Password entered")

                submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                submit_button.click()
                logger.info("Login form submitted")

                # Wait for CAPTCHA and login completion
                logger.info("Waiting for CAPTCHA completion and login process...")
                max_wait_time = 120
                check_interval = 2
                
                start_time = time.time()
                while time.time() - start_time < max_wait_time:
                    if self.check_login_status():
                        logger.info("Successfully logged in!")
                        return True
                    time.sleep(check_interval)
                
                logger.error("Login timeout - couldn't confirm successful login")
                return False
            else:
                logger.info("Already logged in!")
                return True

        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return False
            
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            return False
    
    def check_login_status(self) -> bool:
        """Check if we're logged in by looking for Log Out button."""
        try:
            # Look for Log Out button - this is the most reliable indicator
            logout_button = self.driver.find_elements(By.XPATH, "//button[text()='Log Out']")
            if logout_button and any(btn.is_displayed() for btn in logout_button):
                logger.info("Login confirmed - found Log Out button")
                return True

            # If no Log Out button, check for Select Wallet (indicates not logged in)
            select_wallet = self.driver.find_elements(By.XPATH, "//button[text()='Select Wallet']")
            if select_wallet and any(btn.is_displayed() for btn in select_wallet):
                logger.debug("Found 'Select Wallet' button - not logged in")
                return False

            logger.debug("No definitive login status indicators found")
            return False

        except Exception as e:
            logger.warning(f"Error checking login status: {str(e)}")
            return False
    
    def collect_transactions(self) -> List[Dict]:
        """Collect latest whale transactions."""
        transactions = []
        try:
            # First try to find the Whale Transactions section
            transaction_container = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[text()='Whale Transactions']/following-sibling::div"))
            )
            
            # Get raw text content for debugging
            raw_text = transaction_container.text
            logger.info(f"Found raw transaction data:\n{raw_text}")
            
            # Try to extract structured data from the text
            lines = raw_text.split('\n')
            current_time = None
            
            for line in lines:
                if 'ago' in line:
                    current_time = line
                    continue
                    
                if 'Whale' in line and ('Bought' in line or 'Sold' in line):
                    try:
                        transaction = {
                            'timestamp': current_time,
                            'whale': '',
                            'action': 'Bought' if 'Bought' in line else 'Sold',
                            'amount': 0.0,
                            'token': '',
                            'market_cap': 0.0
                        }
                        
                        # Extract whale name
                        whale_match = re.search(r'(\w+)\s+Whale', line)
                        if whale_match:
                            transaction['whale'] = whale_match.group(1)
                            
                        # Extract amount
                        amount_match = re.search(r'\$(\d+(?:,\d+)*(?:\.\d+)?)', line)
                        if amount_match:
                            transaction['amount'] = float(amount_match.group(1).replace(',', ''))
                            
                        transactions.append(transaction)
                        logger.info(f"Extracted transaction: {transaction}")
                        
                    except Exception as e:
                        logger.warning(f"Failed to parse line: {line}, Error: {str(e)}")
                        continue
                        
                elif 'MC:' in line:
                    if transactions:
                        try:
                            # Extract market cap
                            mc_match = re.search(r'MC:\s*\$([0-9,.]+)([KMB])?', line)
                            if mc_match:
                                number = float(mc_match.group(1).replace(',', ''))
                                multiplier = {
                                    'K': 1000,
                                    'M': 1000000,
                                    'B': 1000000000
                                }.get(mc_match.group(2), 1)
                                transactions[-1]['market_cap'] = number * multiplier
                                
                            # Try to extract token name if present
                            token_text = line.split('MC:')[0].strip()
                            if token_text:
                                transactions[-1]['token'] = token_text
                                
                        except Exception as e:
                            logger.warning(f"Failed to parse market cap line: {line}, Error: {str(e)}")
            
            logger.info(f"Successfully collected {len(transactions)} transactions")
            
        except Exception as e:
            logger.error(f"Error collecting transactions: {str(e)}")
            if 'transaction_container' in locals():
                logger.debug(f"Container HTML: {transaction_container.get_attribute('innerHTML')}")
            
        return transactions
    
    def run(self, duration_hours: float = 24):
        """Run the collector for specified duration."""
        try:
            self.setup_driver()
            login_attempts = 0
            max_login_attempts = 3
            
            while login_attempts < max_login_attempts:
                if self.login():
                    logger.info("Successfully logged in, starting collection...")
                    break
                login_attempts += 1
                if login_attempts < max_login_attempts:
                    logger.warning(f"Login attempt {login_attempts} failed, retrying...")
                    time.sleep(5)
            
            if login_attempts >= max_login_attempts:
                logger.error("Failed to login after multiple attempts")
                return
                
            start_time = datetime.now()
            end_time = start_time + timedelta(hours=duration_hours)
            logger.info(f"Starting collection for {duration_hours} hours")
            
            while datetime.now() < end_time:
                try:
                    transactions = self.collect_transactions()
                    if transactions:
                        logger.info(f"Collected {len(transactions)} transactions")
                        for tx in transactions:
                            logger.info(f"Transaction: {tx}")
                    else:
                        logger.warning("No transactions found in this iteration")
                        
                    time.sleep(int(os.getenv("DATA_COLLECTION_INTERVAL", "10")))
                    
                except Exception as e:
                    logger.error(f"Error during collection: {str(e)}")
                    if not self.check_login_status():
                        logger.warning("Lost session, attempting to login again...")
                        if not self.login():
                            raise Exception("Failed to recover session")
                    time.sleep(5)
                    
        except KeyboardInterrupt:
            logger.info("Collector stopped by user")
        except Exception as e:
            logger.error(f"Collector error: {str(e)}")
        finally:
            if self.driver:
                self.driver.quit()


if __name__ == "__main__":
    collector = AssetDashCollector()
    try:
        collector.run(duration_hours=24)  # Run for 24 hours
    except KeyboardInterrupt:
        print("\nStopping collector...")
    finally:
        if hasattr(collector, 'driver'):
            collector.driver.quit()