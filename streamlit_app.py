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

# 최대 페이지 수 가져오는 함수
def get_max_pages(soup):
    pagination = soup.select_one('div.paging_number_wrap')
    if pagination:
        pages = pagination.find_all('a', class_='snum')
        return int(pages[-1].text) if pages else 1
    return 1

# 제품 정보 크롤링 함수
def crawl_product_info(search_query):
    product_list = []
    
    # 첫 번째 페이지 내용 가져오기
    soup = get_page_content(search_query, 1)
    max_pages = get_max_pages(soup)

    for page_num in range(1, max_pages + 1):
        st.session_state.progress_bar.progress(page_num / max_pages)  # 진행률 표시
        soup = get_page_content(search_query, page_num)
        products = soup.select('li.prod_item')

        for product in products:
            try:
                # 업체명 및 제품명 가져오기
                name_tag = product.select_one('p.prod_name a')
                full_name = name_tag.text.strip() if name_tag else '정보 없음'
                업체명 = full_name.split()[0]  # 공백 전까지 업체명
                제품명 = ' '.join(full_name.split()[1:])  # 첫 공백 이후 제품명

                # 가격 가져오기
                price_tag = product.select_one('p.price_sect a strong')
                price = price_tag.text.strip() if price_tag else '정보 없음'

                # 이미지 URL 가져오기
                image_url_tag = product.select_one('div.thumb_image a img')
                image_url = image_url_tag['src'] if image_url_tag else '정보 없음'

                # 링크 가져오기
                link_tag = product.select_one('div.thumb_image a')
                link = link_tag['href'] if link_tag else '정보 없음'

                # 추가 정보 가져오기
                additional_info_tag = product.select_one('div.spec_list')
                additional_info = additional_info_tag.text.strip() if additional_info_tag else '정보 없음'

                # 등록월 가져오기
                registration_date_tag = product.select_one('div.prod_sub_meta dl.meta_item.mt_date dd')
                registration_date = registration_date_tag.text.strip() if registration_date_tag else '정보 없음'

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
                    '이미지': image_url,
                    '링크': link,
                    '평점': rating,
                    '리뷰 수': review_count,
                    '등록월': registration_date,
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

# 진행률 바 초기화
if search_button:
    st.session_state.progress_bar = st.progress(0)  # 진행률 바 초기화

    st.write(f"'{search_query}' 검색 결과:")
    
    # 크롤링 시작
    product_list = crawl_product_info(search_query)
    
    # 결과를 데이터프레임으로 변환 후 출력
    df = pd.DataFrame(product_list)

    # 하이퍼링크 처리
    df['링크'] = df['링크'].apply(lambda x: f'<a href="{x}" target="_blank">링크</a>')
    
    st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)

    # CSV 파일 다운로드 버튼
    csv = df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="CSV 다운로드",
        data=csv,
        file_name=f'{search_query}_검색결과.csv',
        mime='text/csv'
    )
