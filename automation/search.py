from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from datetime import datetime, timedelta
from urllib.parse import quote
import time
import subprocess
import platform
import csv
import itertools
import os

def initialize(user, password, target, since, until, update_log):

    # Chrome Config
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--disable-gpu") 
    chrome_options.add_argument("--no-sandbox")  
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    # Date parsing
    since_obj = datetime.strptime(since, '%d-%m-%Y')    # to get since_obj.day, since_obj.month, and since_obj.year
    until_obj = datetime.strptime(until, '%d-%m-%Y')    # same

    # Generate or get the necessary files
    downloads_folder = os.path.join(os.getcwd(), 'downloads')

    # Ensure the downloads folder exists, if not, create it
    if not os.path.exists(downloads_folder):
        os.makedirs(downloads_folder)

    # Define the full path for the file
    file_name = f"{target}.csv"
    file_path = os.path.join(downloads_folder, file_name)

    if os.path.exists(file_path):
        update_log(f"The file {file_name} already exists. More posts will be appended to it.")
    else:
        update_log(f"Creating {file_name}.")

    # Get the chrome version to load the correct driver

    def get_chrome_version():
        try:
            system_platform = platform.system()

            if system_platform == 'Windows': # windows
                version = subprocess.check_output(
                    r'reg query "HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon" /v version',
                    shell=True
                )
                version = version.decode('utf-8').strip().split()[-1]

            elif system_platform == 'Linux': # linux
                version = subprocess.check_output(['google-chrome', '--version'])
                version = version.decode('utf-8').strip().split()[-1]

            elif system_platform == 'Darwin':  # macOS
                version = subprocess.check_output(['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '--version'])
                version = version.decode('utf-8').strip().split()[-1]

            else:
                raise Exception(f"Unsupported system: {system_platform}")

            return version

        except Exception as e:
            print(f"Error retrieving Chrome version: {e}")
            return None

    chrome_version = get_chrome_version()

    # Get the driver according to the Chrome version
    if int(chrome_version.split('.')[0]) >= 115:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    else:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager(version=chrome_version).install()), options=chrome_options)

    time.sleep(2)

    wait = WebDriverWait(driver, 10)

    # Login
    driver.get('https://x.com/i/flow/login')
    time.sleep(10)
    x_username = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[autocomplete=username]')))
    x_username.send_keys(f"{user}")
    time.sleep(2)
    login_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[role=button].r-13qz1uu')))
    login_button.click()
    time.sleep(2)
    x_password = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[type=password]')))
    x_password.send_keys(f"{password}")
    login_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid*=Login_Button]')))
    login_button.click()

    time.sleep(10)

    start_date = datetime(since_obj.year, since_obj.month, since_obj.day)
    end_date = datetime(until_obj.year, until_obj.month, until_obj.day)
    day_count = (end_date - start_date).days
    date = start_date
    links = []
    tweets = []

    # Set up WebDriverWait with a 10 seconds timeout
    wait = WebDriverWait(driver, 10)

    # First, scroll to bottom to the page

    def scroll_to_bottom(driver):

        old_position = 0
        new_position = None

        while new_position != old_position:
            # get old scroll position
            old_position = driver.execute_script(
                    ("return (window.pageYOffset !== undefined) ?"
                    " window.pageYOffset : (document.documentElement ||"
                    " document.body.parentNode || document.body);"))

            time.sleep(10)

            # sleep and scroll
            time.sleep(1)
            driver.execute_script((
                    "var scrollingElement = (document.scrollingElement ||"
                    " document.body);scrollingElement.scrollTop ="
                    " scrollingElement.scrollHeight;"))

            # get new position
            new_position = driver.execute_script(
                    ("return (window.pageYOffset !== undefined) ?"
                    " window.pageYOffset : (document.documentElement ||"
                    " document.body.parentNode || document.body);"))

    # Then, scroll again, but retrieving the links and posts

    def new_scroll(driver):

        new_old_position = 0
        new_new_position = None

        while new_new_position != new_old_position:

            actions = ActionChains(driver)

            new_old_position = driver.execute_script(
                    ("return (window.pageYOffset !== undefined) ?"
                    " window.pageYOffset : (document.documentElement ||"
                    " document.body.parentNode || document.body);"))

            actions.send_keys(Keys.SPACE).perform()
            
            try:

                hrefs = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '[data-testid=User-Name] a[role=link][href*=status]')))   
                
                for href in hrefs:
                    link = href.get_attribute('href')
                    if link in links:
                        pass
                    else:
                        links.append(link)
            
                texts = driver.find_elements(By.CSS_SELECTOR, '[data-testid=tweetText]')

                for tweet in texts:
                    post_text = tweet.text
                    if post_text in tweets:
                        pass
                    else:
                        tweets.append(post_text)
            
            except TimeoutException:
                break  # break the loop to stop waiting
            
            time.sleep(2)

            new_new_position = driver.execute_script(
                    ("return (window.pageYOffset !== undefined) ?"
                    " window.pageYOffset : (document.documentElement ||"
                    " document.body.parentNode || document.body);"))

    for i in range(day_count):

        date += timedelta(1)
        yesterday = date - timedelta(1)

        # Build the search URL on X based on the defined parameters
        driver.get(f'https://x.com/search?q=from%3A{quote(target)}%20until%3A{date.strftime("%Y-%m-%d")}%20since%3A{yesterday.strftime("%Y-%m-%d")}&src=typed_query&f=live')
        
        time.sleep(15)  # time needed to fully load

        try:
            scroll_to_bottom(driver) 
            driver.execute_script("window.scrollTo(0, document.body.scrollTop);")  
            new_scroll(driver)
        except Exception as e:
            update_log(f"Error on {yesterday.strftime('%d-%m-%Y')}: {str(e)}. Skipping to the next day.")

        # Check if there are posts, and if so, append them to the CSV file
        if not links or not tweets:
            update_log(f"No posts found for {yesterday.strftime('%d-%m-%Y')}")
        else:
            with open(file_path, 'a') as f:
                writer = csv.writer(f)
                writer.writerows(zip(links, tweets, itertools.repeat(yesterday.strftime('%d-%m-%Y'))))
            
            update_log("Day " + str(yesterday.strftime('%d-%m-%Y')) + " is done!")

        # Clear variables for the next day's loop
        links = []
        tweets = []
        time.sleep(10)

    update_log(f"Scraping for {target} is complete! Enjoy!")

    driver.quit()

