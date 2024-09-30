import os
import requests
import urllib.request
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from PIL import Image
from openpyxl import Workbook
from openpyxl.drawing.image import Image as ExcelImage
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font, Alignment
import streamlit as st

def download_chromedriver():
    url = "https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip"
    response = requests.get(url)
    
    with open("chromedriver.zip", "wb") as file:
        file.write(response.content)

    os.system("unzip chromedriver.zip")
    os.system("chmod +x chromedriver")  # 실행 권한 부여

def go_to_page(driver, search_query, page_num):
    url = f"https://search.danawa.com/dsearch.php?query={search_query}&page={page_num}"
    driver.get(url)

def create_default_image(image_path):
    default_image = Image.new('RGB', (100, 100), color='white')
    default_image.save(image_path)

def clean_filename(filename):
    return re.sub(r'[\/:*?"<>|]', '_', filename)

def main(search_query, start_page, end_page):
    # ChromeDriver가 존재하지 않으면 다운로드
    if not os.path.exists("chromedriver"):
        download_chromedriver()

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')  # 브라우저를 보이지 않게 설정
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    # 드라이버 초기화
    service = ChromeService(executable_path="./chromedriver")  # 경로 확인
    driver = webdriver.Chrome(service=service, options=chrome_options)

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
            # (중략: 크롤링 로직은 기존과 동일)

    today_date = datetime.today().strftime('%Y-%m-%d')
    filename = f"온라인_시장조사_{search_query}_{today_date}.xlsx"

    wb.save(filename)

if __name__ == '__main__':
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
