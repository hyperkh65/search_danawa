import os
import urllib.request
import re
from PIL import Image
from openpyxl import Workbook
from openpyxl.drawing.image import Image as ExcelImage
from openpyxl.styles import Font, Alignment
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import streamlit as st

def go_to_page(driver, search_query, page_num):
    url = f"https://search.danawa.com/dsearch.php?query={search_query}&originalQuery={search_query}&previousKeyword={search_query}&checkedInfo=N&volumeType=allvs&page={page_num}&limit=40&sort=saveDESC&list=list&boost=true&tab=goods&addDelivery=N&coupangMemberSort=N&isInitTireSmartFinder=N&recommendedSort=N&defaultUICategoryCode=15242844&defaultPhysicsCategoryCode=1826%7C58563%7C58565%7C0&defaultVmTab=331&defaultVaTab=45807&isZeroPrice=Y&quickProductYN=N&priceUnitSort=N&priceUnitSortOrder=A"
    driver.get(url)

def resize_image(image_path, width, height):
    img = Image.open(image_path)
    img = img.resize((width, height))
    img.save(image_path)

def create_default_image(image_path):
    default_image = Image.new('RGB', (100, 100), color='white')
    default_image.save(image_path)

def clean_filename(filename):
    return re.sub(r'[\/:*?"<>|]', '_', filename)

def main(search_query, start_page, end_page):
    # ChromeDriverManager를 사용하여 ChromeDriver 설치
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')  # Headless 모드
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')  # GPU 사용 비활성화
    chrome_options.add_argument('--window-size=1920,1080')  # 가상 화면 크기 설정

    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)

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
                product_title = container.find_element(By.CSS_SELECTOR, 'div.prod_info > p > a').text
                product_price = container.find_element(By.CSS_SELECTOR,
                                                       'div.prod_pricelist > ul > li > p.price_sect > a > strong').text
                registration_month = container.find_element(By.CSS_SELECTOR,
                                                            'div.prod_sub_info > div.prod_sub_meta > dl.meta_item.mt_date > dd').text
                rating = container.find_element(By.CSS_SELECTOR,
                                                'div.prod_sub_info > div.prod_sub_meta > dl.meta_item.mt_comment > dd > div.cnt_star > div.point_num > strong').text
                review_count = container.find_element(By.CSS_SELECTOR,
                                                      'div.prod_sub_info > div.prod_sub_meta > dl.meta_item.mt_comment > dd > div.cnt_opinion > a > strong').text
            except:
                product_price = "가격 정보 없음"
                registration_month = "등록월 정보 없음"
                rating = "평점 정보 없음"
                review_count = "리뷰 수 정보 없음"

            product_image_tag = container.find_element(By.CSS_SELECTOR, 'div.thumb_image > a > img')
            lazyloaded_url = product_image_tag.get_attribute('data-src')

            if lazyloaded_url is not None:
                if lazyloaded_url.startswith('//'):
                    lazyloaded_url = 'https:' + lazyloaded_url

                image_filename = clean_filename(product_title) + ".png"
                image_path = os.path.join(image_directory, image_filename)
                urllib.request.urlretrieve(lazyloaded_url, image_path)
                resize_image(image_path, width=100, height=100)
                img = ExcelImage(image_path)
            else:
                img = ExcelImage(default_image_path)

            try:
                additional_info = container.find_element(By.CSS_SELECTOR, 'div.spec_list').text
            except:
                additional_info = "부가정보 없음"

            product_link = container.find_element(By.CSS_SELECTOR, 'a.thumb_link').get_attribute('href')

            ws.append([product_title, product_price, '', additional_info, product_link, registration_month, rating,
                       review_count])
            ws.add_image(img, f'C{ws.max_row}')
            link_cell = ws[f'E{ws.max_row}']
            link_cell.value = "제품 링크"
            link_cell.font = Font(color='0563C1', underline='single')
            link_cell.alignment = Alignment(horizontal='center')
            ws[f'E{ws.max_row}'].hyperlink = product_link
            ws[f'E{ws.max_row}'].style = 'Hyperlink'

    today_date = datetime.today().strftime('%Y-%m-%d')
    filename = f"온라인_시장조사_{search_query}_{today_date}.xlsx"

    wb.save(filename)
    st.success(f"{filename} 파일이 생성되었습니다.")

    # Streamlit에서 다운로드 버튼을 추가
    with open(filename, "rb") as f:
        st.download_button("다운로드", f, filename=filename)

if __name__ == '__main__':
    st.title("온라인 시장 조사")
    search_query = st.text_input("검색어를 입력하세요:")
    start_page = st.number_input("시작 페이지를 입력하세요:", min_value=1, value=1)
    end_page = st.number_input("종료 페이지를 입력하세요:", min_value=1, value=1)

    if st.button("검색"):
        if search_query:
            main(search_query, start_page, end_page)
        else:
            st.warning("검색어를 입력해주세요.")
