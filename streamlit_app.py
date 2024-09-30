from bs4 import BeautifulSoup
from PIL import Image
from openpyxl import Workbook
from openpyxl.drawing.image import Image as ExcelImage
import requests
import os
import re
from datetime import datetime

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
    wb = Workbook()
    ws = wb.active
    ws.append(['상품', '가격', '이미지', '부가정보', '링크', '등록월', '평점', '리뷰 수'])

    image_directory = 'product_images'
    if not os.path.exists(image_directory):
        os.makedirs(image_directory)

    default_image_path = os.path.join(image_directory, "default_image.png")
    create_default_image(default_image_path)

    for page_num in range(start_page, end_page + 1):
        url = f"https://search.danawa.com/dsearch.php?query={search_query}&page={page_num}"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        product_containers = soup.select('div.prod_main_info')

        for container in product_containers:
            try:
                product_title = container.select_one('div.prod_info > p > a').text.strip()
                product_price = container.select_one('div.prod_pricelist > ul > li > p.price_sect > a > strong').text.strip()
                registration_month = container.select_one('div.prod_sub_info > div.prod_sub_meta > dl.meta_item.mt_date > dd').text.strip()
                rating = container.select_one('div.prod_sub_info > div.prod_sub_meta > dl.meta_item.mt_comment > dd > div.cnt_star > div.point_num > strong').text.strip()
                review_count = container.select_one('div.prod_sub_info > div.prod_sub_meta > dl.meta_item.mt_comment > dd > div.cnt_opinion > a > strong').text.strip()
            except:
                product_price = "가격 정보 없음"
                registration_month = "등록월 정보 없음"
                rating = "평점 정보 없음"
                review_count = "리뷰 수 정보 없음"

            product_image_tag = container.select_one('div.thumb_image > a > img')
            lazyloaded_url = product_image_tag['data-src'] if product_image_tag and 'data-src' in product_image_tag.attrs else None

            if lazyloaded_url:
                if lazyloaded_url.startswith('//'):
                    lazyloaded_url = 'https:' + lazyloaded_url

                image_filename = clean_filename(product_title) + ".png"
                image_path = os.path.join(image_directory, image_filename)

                # 이미지 다운로드
                try:
                    img_data = requests.get(lazyloaded_url).content
                    with open(image_path, 'wb') as handler:
                        handler.write(img_data)
                    resize_image(image_path, width=100, height=100)
                    img = ExcelImage(image_path)
                except Exception as e:
                    print(f"이미지 다운로드 실패: {e}")
                    img = ExcelImage(default_image_path)
            else:
                img = ExcelImage(default_image_path)

            try:
                additional_info = container.select_one('div.spec_list').text.strip()
            except:
                additional_info = "부가정보 없음"

            product_link = container.select_one('a.thumb_link')['href']

            ws.append([product_title, product_price, '', additional_info, product_link, registration_month, rating, review_count])
            ws.add_image(img, f'C{ws.max_row}')

    today_date = datetime.today().strftime('%Y-%m-%d')
    filename = f"온라인_시장조사_{search_query}_{today_date}.xlsx"
    wb.save(filename)

if __name__ == '__main__':
    search_query = input("검색어를 입력하세요: ")
    start_page = int(input("시작 페이지를 입력하세요: "))
    end_page = int(input("종료 페이지를 입력하세요: "))
    main(search_query, start_page, end_page)
