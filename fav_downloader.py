import os
import re
import sys
import time
import shutil
import requests
import pickle
from selenium import webdriver
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
from loguru import logger
from bs4 import BeautifulSoup

FORMAT = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{thread.name}</cyan>:<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
logger.remove()
logger.add(sys.stdout, level='TRACE', format=FORMAT)
logger.add('.logs/app.log', level='TRACE', format=FORMAT,
           rotation='10 MB', compression='zip', enqueue=True)
logger.add('.logs/error.log', level='ERROR', format=FORMAT,
           rotation='10 MB', compression='zip', enqueue=True)


if __name__ == '__main__':
    load_dotenv()
    logger.info('starting...')

    login = os.environ['LOGIN']

    favorites_path = os.environ['FAVORITES_PATH']

    if not os.path.exists(favorites_path):
        logger.warning('favorites path on exist')
        os.mkdir(favorites_path)

    page = 1

    url = f'https://flickr.com/photos/{login}/favorites/page{page}'

    logger.info('load chrome')

    options = webdriver.ChromeOptions()
    # options.headless = True
    # options.add_argument('--headless')
    # options.add_argument('user-data-dir=selenium')
    options.page_load_strategy = 'none'
    chrome_path = ChromeDriverManager().install()
    chrome_service = Service(chrome_path)

    driver = Chrome(options=options, service=chrome_service)
    driver.implicitly_wait(5)

    next_page_url = url

    while next_page_url != '':
        logger.info('get page ' + next_page_url)
        driver.get(next_page_url)
        time.sleep(5)

        # pickle.dump(driver.get_cookies(), open("cookies.pkl", "wb"))

        cookies = pickle.load(open("cookies.pkl", "rb"))
        for cookie in cookies:
            driver.add_cookie(cookie)

        driver.get(next_page_url)

        time.sleep(5)
        for i in range(5):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
        detail_urls = []
        contents = driver.find_elements(By.CSS_SELECTOR, 'a[class*="overlay"')
        for content in contents:
            detail_url = content.get_attribute('href')
            detail_urls.append(detail_url)
        logger.info(f'found {len(detail_urls)} images ')

        try:
            next_page_url = contents = driver.find_element(By.CSS_SELECTOR, 'a[data-track*="paginationRightClick"').get_attribute('href')
            logger.info(f'next page {next_page_url}')
        except:
            next_page_url = ''
            logger.warning('next page not found')

        for j, detail_url in enumerate(detail_urls):
            logger.info(f'get detail [{len(detail_urls)}:{j}] {detail_url}')
            click = False
            for i in range(3):
                try:
                    if not click:
                        driver.get(detail_url)
                        try:
                            element = WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located(
                                    (By.CSS_SELECTOR, 'div[class*="photo-notes-scrappy-view"]'))
                            )
                        finally:
                            pass
                        img_content = driver.find_element(By.CSS_SELECTOR, 'div[class*="photo-notes-scrappy-view"]')
                        time.sleep(1)
                        logger.debug('try click element')
                        img_content.click()
                        click = True
                except:
                    pass
            if click:
                img_url = ''
                try:
                    img_url = driver.find_element(By.CSS_SELECTOR, 'img[class*="zoom-large"]').get_attribute('src')
                    img_url = driver.find_element(By.CSS_SELECTOR, 'img[class*="zoom-xlarge"]').get_attribute('src')
                except:
                    pass
                if img_url != '':
                    file_name = img_url.split('/')[-1]
                    logger.info(f'get image {file_name}')
                    if not os.path.exists(os.path.join(favorites_path, file_name)):
                        img = requests.get(img_url)
                        if img.status_code == 200:
                            with open(os.path.join(favorites_path, file_name), 'wb') as f:
                                f.write(img.content)
                                logger.info('image saved')
                                f.close()
                    else:
                        logger.info('image already exists')

                logger.info('image url ' + img_url)

    logger.info('done!')
