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
def crawl_product_info(search_query):
    product_list = []
    
    # 최대 페이지 수 자동으로 추출
    soup = get_page_content(search_query, 1)
    max_pages = len(soup.select('div.paging_number_wrap a'))  # 최대 페이지 수 추출

    for page_num in range(1, max_pages + 1):
        st.progress(page_num / max_pages)  # 진행률 표시
        soup = get_page_content(search_query, page_num)
        products = soup.select('li.prod_item')

        for product in products:
            try:
                # 제품명 가져오기
                name_tag = product.select_one('p.prod_name a')
                name = name_tag.text.strip() if name_tag else '정보 없음'
                
                # 업체명 추출
                업체명 = name.split(' ')[0]  # 첫 번째 공백 전까지 잘라서 업체명으로 사용
                제품명 = ' '.join(name.split(' ')[1:])  # 첫 번째 공백 이후 제품명

                # 가격 가져오기
                price_tag = product.select_one('p.price_sect a strong')
                price = price_tag.text.strip() if price_tag else '정보 없음'

                # 이미지 URL 가져오기
                image_tag = product.select_one('div.thumb_image a img')
                image_url = image_tag['src'] if image_tag else '정보 없음'
                
                # URL 수정: http 또는 https로 시작하도록 설정
                if image_url.startswith("//"):
                    image_url = "https:" + image_url

                # 링크 가져오기
                link_tag = product.select_one('div.thumb_image a')
                link = link_tag['href'] if link_tag else '정보 없음'

                # 추가 정보, 등록월, 평점, 리뷰 수 가져오기
                additional_info_tag = product.select_one('div.spec_list')
                additional_info = additional_info_tag.text.strip() if additional_info_tag else '정보 없음'

                registration_date_tag = product.select_one('div.prod_sub_meta > dl.meta_item.mt_date > dd')
                registration_date = registration_date_tag.text.strip() if registration_date_tag else '정보 없음'

                rating_tag = product.select_one('div.star-single > span.text__score')
                rating = rating_tag.text.strip() if rating_tag else '정보 없음'

                review_count_tag = product.select_one('div.text__review > span.text__number')
                review_count = review_count_tag.text.strip() if review_count_tag else '정보 없음'

                # 데이터 저장
                product_list.append({
                    '업체명': 업체명,
                    '제품명': 제품명,
                    '추가정보': additional_info,
                    '가격': price,
                    '이미지': image_url,
                    '링크': link,
                    '평점': rating,
                    '리뷰 수': review_count,
                    '등록월': registration_date
                })

            except Exception as e:
                print(f"Error processing product: {e}")

    return product_list

# Streamlit 애플리케이션 설정
st.set_page_config(layout="wide")

# 왼쪽 옵션 패널 만들기
with st.sidebar:
    st.title("검색 옵션")
    search_query = st.text_input("검색어 입력", "노트북")
    search_button = st.button("검색")

# 검색 버튼이 눌렸을 때
if search_button:
    st.write(f"'{search_query}' 검색 결과:")
    
    # 크롤링 시작
    product_list = crawl_product_info(search_query)
    
    # 결과를 데이터프레임으로 변환 후 출력
    df = pd.DataFrame(product_list)
    st.dataframe(df)

    # 각 제품의 이미지를 크게 표시
    st.subheader("제품 이미지")
    for product in product_list:
        st.image(product['이미지'], caption=product['제품명'], use_column_width='auto')  # 이미지 크기 자동 조정

    # CSV 파일 다운로드 버튼
    csv = df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="CSV 다운로드",
        data=csv,
        file_name=f'{search_query}_검색결과.csv',
        mime='text/csv'
    )
