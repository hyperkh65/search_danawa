import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# 제품 정보를 저장할 리스트
products = []

# 진행률 표시 함수
def update_progress_bar(total, completed):
    percent = (completed / total) * 100
    progress_text = f"{completed}/{total} ({percent:.2f}%)"
    st.session_state.progress_bar.progress(percent)
    st.session_state.progress_text.text(progress_text)

# 제품 정보 추출 함수
def extract_product_info(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    product_list = soup.select('div.prod_info')
    for product in product_list:
        try:
            name = product.select_one('p.prod_name > a').text.strip()
            price = product.select_one('div.prod_pricelist > ul > li > p.price_sect > a > strong').text.strip()
            image_url = product.select_one('div.thumb_image > a > img')['src']
            link = product.select_one('div.thumb_image > a')['href']
            additional_info = product.select_one('div.spec_list').text.strip()
            registration_month = product.select_one('div.prod_sub_meta > dl.meta_item.mt_date > dd').text.strip()
            rating = product.select_one('div.star-single > span.text__score').text.strip()
            review_count = product.select_one('div.text__review > span.text__number').text.strip()

            products.append({
                "Product Name": name,
                "Price": price,
                "Image URL": image_url,
                "Link": link,
                "Additional Info": additional_info,
                "Registration Month": registration_month,
                "Rating": rating,
                "Review Count": review_count,
            })
        except Exception as e:
            st.error(f"Error processing product: {e}")

# 페이지 크롤링 함수
def crawl_pages(base_url, total_pages):
    for page in range(1, total_pages + 1):
        url = f"{base_url}?page={page}"
        extract_product_info(url)
        update_progress_bar(total_pages, page)
        time.sleep(1)  # 요청 간의 지연

# Streamlit 앱 구성
st.set_page_config(page_title="Product Scraper", layout="wide")

# 왼쪽 옵션 패널
st.sidebar.header("Search Options")
search_query = st.sidebar.text_input("Search Query")
search_button = st.sidebar.button("Search")

# 진행률 표시
if "progress_bar" not in st.session_state:
    st.session_state.progress_bar = st.empty()
if "progress_text" not in st.session_state:
    st.session_state.progress_text = st.empty()

# 결과 표시
if search_button:
    base_url = "http://example.com/products"  # 실제 URL로 변경
    total_pages = 10  # 페이지 수 설정
    crawl_pages(base_url, total_pages)
    
    # DataFrame으로 변환
    df = pd.DataFrame(products)
    
    # CSV 다운로드
    csv_file = df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button("Download CSV", csv_file, "products.csv", "text/csv")

    # 결과 표시
    st.write(df)

