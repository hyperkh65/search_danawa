import os
import requests
import urllib.request
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from PIL import Image
from openpyxl import Workbook
from openpyxl.drawing.image import Image as ExcelImage
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font, Alignment
from bs4 import BeautifulSoup  # 이 줄에서 모듈이 필요합니다.

def download_chromedriver():
    url = "https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip"
    response = requests.get(url)
    
    with open("chromedriver.zip", "wb") as file:
        file.write(response.content)

    os.system("unzip chromedriver.zip")
    os.system("chmod +x chromedriver")  # 실행 권한 부여

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
    # ChromeDriver가 존재하지 않으면 다운로드
    if not os.path.exists("chromedriver"):
        download_chromedriver()

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')  # 브라우저를 보이지 않게 설정
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    # 드라이버 초기화
    driver = webdriver.Chrome(service=ChromeService("chromedriver"), options=chrome_options)

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
    
    # Google Colab에서 다운로드 링크를 생성하여 파일 다운로드 (필요 시 주석 해제)
    # from google.colab import files
    # files.download(filename)  

if __name__ == '__main__':
    search_query = input("검색어를 입력하세요: ")
    start_page = int(input("시작 페이지를 입력하세요: "))
    end_page = int(input("종료 페이지를 입력하세요: "))
    main(search_query, start_page, end_page)
