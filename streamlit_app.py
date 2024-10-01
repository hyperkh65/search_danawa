import streamlit as st
import requests
from bs4 import BeautifulSoup
from openpyxl import Workbook
from openpyxl.drawing.image import Image as ExcelImage
from PIL import Image
import io

def fetch_product_info(search_query):
    # 예시 URL, 실제 크롤링할 URL로 변경 필요
    url = f"https://search.danawa.com/dsearch.php?query={search_query}"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    products = []
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
                image_path = f"{title}.png"
                image.save(image_path)  # 이미지를 저장할 필요는 없지만, 경로를 임시로 지정할 수 있음
                img = ExcelImage(image_path)
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
if st.button("검색"):
    products = fetch_product_info(search_query)
    if products:
        wb = create_excel_with_images(products)
        excel_file = "제품정보.xlsx"
        wb.save(excel_file)

        # Streamlit에서 파일 다운로드
        with open(excel_file, "rb") as f:
            st.download_button("엑셀 파일 다운로드", f, file_name=excel_file)
    else:
        st.warning("검색 결과가 없습니다.")
