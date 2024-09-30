import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# 상품 정보를 저장할 리스트
product_data = []

# 진행율을 추적하는 함수
def update_progress(progress, total_pages):
    percent_complete = (progress / total_pages) * 100
    st.write(f"진행율: {progress}/{total_pages} ({percent_complete:.2f}%)", end='\r')

# 단일 페이지에서 제품 정보 크롤링 함수
def extract_product_info(page_url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36"
    }
    response = requests.get(page_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    products = soup.find_all('div', class_='prod_main_info')

    for product in products:
        try:
            name = product.find('p', class_='prod_name').text.strip()
            price = product.find('p', class_='price_sect').text.strip()
            link = product.find('p', class_='prod_name').find('a')['href']
            image = product.find('img')['src']
            details = product.find('div', class_='spec_list').text.strip()
            reg_date = product.find('span', class_='reg_date').text.strip() if product.find('span', class_='reg_date') else 'N/A'
            reviews = product.find('span', class_='count').text.strip() if product.find('span', class_='count') else 'N/A'
            rating = product.find('em', class_='rating').text.strip() if product.find('em', class_='rating') else 'N/A'
            interest = product.find('span', class_='wish_cnt').text.strip() if product.find('span', class_='wish_cnt') else 'N/A'

            product_data.append({
                '상품명': name,
                '가격': price,
                '링크': link,
                '이미지': image,
                '상세정보': details,
                '등록월': reg_date,
                '별점': rating,
                '리뷰수': reviews,
                '관심상품수': interest
            })

        except Exception as e:
            print(f"Error processing product: {e}")

# 페이지별로 크롤링을 실행
def crawl_all_pages(search_query, num_pages):
    base_url = "https://search.danawa.com/dsearch.php"
    for page in range(1, num_pages + 1):
        params = {
            'query': search_query,
            'page': page
        }
        page_url = f"{base_url}?query={search_query}&page={page}"
        extract_product_info(page_url)
        
        # 진행율 업데이트
        update_progress(page, num_pages)

# CSV 저장 함수
def save_to_csv(product_data, file_name):
    df = pd.DataFrame(product_data)
    df.to_csv(file_name, index=False, encoding='utf-8-sig')  # utf-8-sig로 한글 깨짐 방지

# Streamlit 앱
def main():
    st.title('다나와 상품 크롤러')
    
    # 왼쪽 옵션 패널
    search_query = st.sidebar.text_input('검색어 입력', value='LED 다운라이트')
    num_pages = st.sidebar.number_input('페이지 수', min_value=1, max_value=20, value=5)
    
    if st.sidebar.button('검색'):
        product_data.clear()
        crawl_all_pages(search_query, num_pages)

        # 결과 출력
        if product_data:
            df = pd.DataFrame(product_data)
            st.dataframe(df)
            
            # CSV 파일로 저장
            if st.button('CSV로 저장'):
                save_to_csv(product_data, 'products.csv')
                st.success('CSV 저장 완료!')

if __name__ == "__main__":
    main()
