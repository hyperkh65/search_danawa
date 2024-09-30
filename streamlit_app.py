import os
import requests
import urllib.request
import re
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from openpyxl import Workbook
import streamlit as st
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image

def get_website_content(url):
    driver = None
    try:
        options = Options()
        options.add_argument('--headless')  # 브라우저를 보이지 않게 설정
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1200')
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(url)
        time.sleep(5)
        html_doc = driver.page_source
        soup = BeautifulSoup(html_doc, "html.parser")
        return soup.get_text()
    except Exception as e:
        st.write(f"DEBUG:INIT_DRIVER:ERROR:{e}")
    finally:
        if driver is not None:
            driver.quit()
    return None

def go_to_page(driver, search_query, page_num):
    url = f"https://search.danawa.com/dsearch.php?query={search_query}&page={page_num}"
    driver.get(url)

def create_default_image(image_path):
    default_image = Image.new('RGB', (100, 100), color='white')
    default_image.save(image_path)

def clean_filename(filename):
    return re.sub(r'[\/:*?"<>|]', '_', filename)

def main(search_query, start_page, end_page):
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # 브라우저를 보이지 않게 설정
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    wb = Workbook()
    ws = wb.active
    ws.append(['상품', '가격', '이미지', '부가정보', '링크', '등록월', '평점', '리뷰 수'])

    image_directory = 'product_images'
    if not os.path.exists(image_directory):
        os.makedirs(image_directory)

    default_image_path = os.path.join(image_directory, "default_image.png")
    create_default_image(default_image_path)

    for page_num in range(start_page, end_page + 1):
        go_to_page(driver, search_query, page_num)

        product_containers = driver.find_elements(By.CSS_SELECTOR, 'div.prod_main_info')

        for container in product_containers:
            try:
                product_name = container.find_element(By.CSS_SELECTOR, 'p.prod_name').text
                price = container.find_element(By.CSS_SELECTOR, 'p.price').text
                link = container.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')

                image_url = container.find_element(By.CSS_SELECTOR, 'img').get_attribute('src')
                if not image_url:
                    image_path = default_image_path
                else:
                    image_name = clean_filename(product_name) + ".png"
                    image_path = os.path.join(image_directory, image_name)
                    urllib.request.urlretrieve(image_url, image_path)

                additional_info = container.find_element(By.CSS_SELECTOR, 'p.info').text
                registration_date = datetime.today().strftime('%Y-%m-%d')
                rating = container.find_element(By.CSS_SELECTOR, 'span.rating').text if container.find_elements(By.CSS_SELECTOR, 'span.rating') else "N/A"
                review_count = container.find_element(By.CSS_SELECTOR, 'span.review_count').text if container.find_elements(By.CSS_SELECTOR, 'span.review_count') else "0"

                ws.append([product_name, price, image_path, additional_info, link, registration_date, rating, review_count])

            except Exception as e:
                st.write(f"Error processing product: {e}")

    today_date = datetime.today().strftime('%Y-%m-%d')
    filename = f"온라인_시장조사_{search_query}_{today_date}.xlsx"
    wb.save(filename)

    driver.quit()  # 드라이버 종료

# Streamlit UI 설정
st.title("Streamlit과 Selenium 웹 크롤링")
search_query = st.text_input("검색어를 입력하세요:")
start_page = st.number_input("시작 페이지를 입력하세요:", min_value=1, value=1)
end_page = st.number_input("종료 페이지를 입력하세요:", min_value=1, value=2)

if st.button("데이터 크롤링 시작"):
    if search_query:
        main(search_query, start_page, end_page)
        st.success("크롤링이 완료되었습니다.")
    else:
        st.error("검색어를 입력하세요.")
