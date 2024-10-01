import streamlit as st
import requests
from bs4 import BeautifulSoup
from openpyxl import Workbook
from openpyxl.drawing.image import Image as ExcelImage
from PIL import Image
import io
import os

def go_to_page(search_query, page_num):
    url = f"https://search.danawa.com/dsearch.php?query={search_query}&page={page_num}"
    return url

def fetch_product_info(search_query, start_page, end_page):
    products = []
    
    for page_num in range(start_page, end_page + 1):
        url = go_to_page(search_query, page_num)
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')

        product_containers = soup.select('div.prod_main_info')
        for container in product_containers:
            title = container.select_one('div.prod_info > p > a').text.strip()
            price = container.select_one('div.prod_pricelist > ul > li > p.price_sect > a > strong').text.strip()
            
            # 이미지 URL 가져오기
            image_tag = container.select_one('div.thumb_image > a > img')
            image_url = image_tag.get('data-src') if image_tag else None
            if image_url and image_url.startswith('//'):
                image_url = 'https:' + image_url
            
            products.append({
                'title': title,
                'price': price,
                'image_url': image_url
            })

    return products

def create_excel_with_images(products):
    wb = Workbook()
    ws = wb.active
    ws.append(['상품', '가격', '이미지'])

    for product in products:
        title = product['title']
        price = product['price']
        image_url = product['image_url']

        # 이미지 다운로드
        if image_url:
            try:
                image_response = requests.get(image_url)
                image = Image.open(io.BytesIO(image_response.content))
                img = ExcelImage(io.BytesIO(image_response.content))
            except Exception as e:
                st.warning(f"이미지 다운로드 실패: {e}")
                img = None
        else:
            img = None

        ws.append([title, price, ''])
        if img:
            ws.add_image(img, f'C{ws.max_row}')

    return wb

# Streamlit 애플리케이션 코드
st.title("제품 검색 및 엑셀 저장")
search_query = st.text_input("검색어를 입력하세요:")
start_page = st.number_input("시작 페이지", min_value=1, value=1)
end_page = st.number_input("종료 페이지", min_value=1, value=1)

if st.button("검색"):
    if end_page < start_page:
        st.warning("종료 페이지는 시작 페이지보다 크거나 같아야 합니다.")
    else:
        products = fetch_product_info(search_query, start_page, end_page)
        if products:
            wb = create_excel_with_images(products)
            excel_file = "제품정보.xlsx"
            wb.save(excel_file)

            # Streamlit에서 파일 다운로드
            with open(excel_file, "rb") as f:
                st.download_button("엑셀 파일 다운로드", f, file_name=excel_file)
        else:
            st.warning("검색 결과가 없습니다.")
