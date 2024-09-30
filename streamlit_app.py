import streamlit as st
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import chromedriver_autoinstaller
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime
import urllib.request
import re
import io
import base64

def get_driver():
    chromedriver_autoinstaller.install()
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    return webdriver.Chrome(options=options)

def go_to_page(driver, search_query, page_num):
    url = f"https://search.danawa.com/dsearch.php?query={search_query}&page={page_num}"
    driver.get(url)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'div.prod_main_info'))
    )

def clean_filename(filename):
    return re.sub(r'[\/:*?"<>|]', '_', filename)

def main(search_query, start_page, end_page):
    driver = get_driver()
    data = []

    for page_num in range(start_page, end_page + 1):
        go_to_page(driver, search_query, page_num)
        product_containers = driver.find_elements(By.CSS_SELECTOR, 'div.prod_main_info')

        for container in product_containers:
            try:
                product_name = container.find_element(By.CSS_SELECTOR, 'p.prod_name').text
                price = container.find_element(By.CSS_SELECTOR, 'p.price').text
                link = container.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
                image_url = container.find_element(By.CSS_SELECTOR, 'img').get_attribute('src')
                additional_info = container.find_element(By.CSS_SELECTOR, 'p.info').text
                registration_date = datetime.today().strftime('%Y-%m-%d')
                rating = container.find_element(By.CSS_SELECTOR, 'span.rating').text if container.find_elements(By.CSS_SELECTOR, 'span.rating') else "N/A"
                review_count = container.find_element(By.CSS_SELECTOR, 'span.review_count').text if container.find_elements(By.CSS_SELECTOR, 'span.review_count') else "0"

                data.append([product_name, price, image_url, additional_info, link, registration_date, rating, review_count])

            except Exception as e:
                st.write(f"Error processing product: {e}")

    driver.quit()

    df = pd.DataFrame(data, columns=['상품', '가격', '이미지 URL', '부가정보', '링크', '등록월', '평점', '리뷰 수'])
    return df

def get_table_download_link(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="danawa_crawling_results.csv">Download CSV File</a>'
    return href

# Streamlit UI 설정
st.title("다나와 웹 크롤링")
search_query = st.text_input("검색어를 입력하세요:")
start_page = st.number_input("시작 페이지를 입력하세요:", min_value=1, value=1)
end_page = st.number_input("종료 페이지를 입력하세요:", min_value=1, value=2)

if st.button("데이터 크롤링 시작"):
    if search_query:
        with st.spinner('크롤링 중...'):
            df = main(search_query, start_page, end_page)
        st.success("크롤링이 완료되었습니다.")
        st.dataframe(df)
        st.markdown(get_table_download_link(df), unsafe_allow_html=True)
    else:
        st.error("검색어를 입력하세요.")
