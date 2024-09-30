import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

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
    
    # 최대 페이지 수를 찾는 로직 추가
    soup = get_page_content(search_query, 1)
    max_pages = int(soup.select_one('div.paging_number_wrap a:last-child')['data-page'])
    
    for page_num in range(1, max_pages + 1):
        soup = get_page_content(search_query, page_num)
        products = soup.select('li.prod_item')

        for product in products:
            try:
                # 업체명 및 제품명 가져오기
                name_tag = product.select_one('p.prod_name a')
                name = name_tag.text.strip() if name_tag else '정보 없음'
                업체명 = name.split()[0]  # 첫 번째 공백 전까지 잘라서 업체명으로 사용
                제품명 = ' '.join(name.split()[1:])  # 첫 번째 공백 이후의 텍스트

                # 가격 가져오기
                price_tag = product.select_one('p.price_sect a strong')
                price = price_tag.text.strip() if price_tag else '정보 없음'

                # 이미지 URL 가져오기
                img_tag = product.select_one('div.thumb_image a img')
                img_url = img_tag['src'] if img_tag else '정보 없음'

                # 링크 가져오기
                link_tag = product.select_one('div.thumb_image a')
                link = link_tag['href'] if link_tag else '정보 없음'

                # 추가 정보 가져오기
                additional_info_tag = product.select_one('div.spec_list')
                additional_info = additional_info_tag.text.strip() if additional_info_tag else '정보 없음'

                # 등록월 가져오기
                reg_date_tag = product.select_one('div.prod_sub_meta dl.meta_item.mt_date dd')
                reg_date = reg_date_tag.text.strip() if reg_date_tag else '정보 없음'

                # 평점 가져오기
                rating_tag = product.select_one('div.star-single span.text__score')
                rating = rating_tag.text.strip() if rating_tag else '정보 없음'

                # 리뷰 수 가져오기
                review_count_tag = product.select_one('div.text__review span.text__number')
                review_count = review_count_tag.text.strip() if review_count_tag else '정보 없음'

                # 데이터 저장
                product_list.append({
                    '업체명': 업체명,
                    '제품명': 제품명,
                    '추가 정보': additional_info,
                    '가격': price,
                    '이미지': img_url,
                    '링크': link,
                    '평점': rating,
                    '리뷰 수': review_count,
                    '등록월': reg_date
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

    # 링크 열에 하이퍼링크 추가
    df['링크'] = df['링크'].apply(lambda x: f'<a href="{x}" target="_blank">링크</a>')

    # Streamlit에서 HTML을 표시하기 위해 마크다운 사용
    st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)

    # CSV 파일 다운로드 버튼
    csv = df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="CSV 다운로드",
        data=csv,
        file_name=f'{search_query}_검색결과.csv',
        mime='text/csv'
    )
