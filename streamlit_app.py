import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time

# 페이지 컨텐츠를 받아오는 함수
def get_page_content(search_query, page_num):
    url = f"https://search.danawa.com/dsearch.php?query={search_query}&page={page_num}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    return BeautifulSoup(response.content, 'html.parser')

# 제품 정보 크롤링 함수
def crawl_product_info(search_query, max_pages):
    product_list = []
    
    for page_num in range(1, max_pages + 1):
        st.progress(page_num / max_pages)  # 진행률 표시
        soup = get_page_content(search_query, page_num)
        products = soup.select('li.prod_item')

        for product in products:
            try:
                # 제품명 가져오기
                name_tag = product.select_one('p.prod_name a')
                name = name_tag.text.strip() if name_tag else '정보 없음'

                # 가격 가져오기
                price_tag = product.select_one('p.price_sect a strong')
                price = price_tag.text.strip() if price_tag else '정보 없음'

                # 데이터 저장
                product_list.append({'제품명': name, '가격': price})

            except Exception as e:
                print(f"Error processing product: {e}")

    return product_list

# Streamlit 애플리케이션 설정
st.set_page_config(layout="wide")

# 왼쪽 옵션 패널 만들기
with st.sidebar:
    st.title("검색 옵션")
    search_query = st.text_input("검색어 입력", "노트북")
    max_pages = st.number_input("최대 페이지 수", min_value=1, max_value=100, value=5)
    search_button = st.button("검색")

# 검색 버튼이 눌렸을 때
if search_button:
    st.write(f"'{search_query}' 검색 결과:")
    
    # 크롤링 시작
    product_list = crawl_product_info(search_query, max_pages)
    
    # 결과를 데이터프레임으로 변환 후 출력
    df = pd.DataFrame(product_list)
    st.dataframe(df)

    # CSV 파일 다운로드 버튼
    csv = df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="CSV 다운로드",
        data=csv,
        file_name=f'{search_query}_검색결과.csv',
        mime='text/csv'
    )
