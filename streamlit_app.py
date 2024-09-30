import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import base64

# 페이지 컨텐츠를 받아오는 함수
def get_page_content(search_query, page_num):
    url = f"https://search.danawa.com/dsearch.php?query={search_query}&page={page_num}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    return BeautifulSoup(response.content, 'html.parser')

# 마지막 페이지 번호를 구하는 함수
def get_last_page_number(soup):
    paging = soup.select('div.paging_number_wrap a')
    if paging:
        return int(paging[-1].get('data-page'))
    return 1  # 페이지 번호가 없을 경우 첫 페이지만 있는 것으로 간주

# 텍스트에서 불필요한 공백을 제거하는 함수
def clean_text(text):
    return re.sub(r'\s+', ' ', text).strip()

# 크롤링 수행하는 함수
def main(search_query):
    data = []
    
    # 첫 번째 페이지에서 마지막 페이지 번호를 파악
    first_page_soup = get_page_content(search_query, 1)
    last_page = get_last_page_number(first_page_soup)
    
    st.write(f"총 {last_page} 페이지 크롤링 중...")
    
    # 각 페이지 순회하면서 크롤링 수행
    for page_num in range(1, last_page + 1):
        soup = get_page_content(search_query, page_num)
        product_containers = soup.select('div.prod_main_info')
        
        for container in product_containers:
            try:
                product_name = clean_text(container.select_one('p.prod_name a').text)
                price = clean_text(container.select_one('p.price_sect a strong').text)
                link = "https:" + container.select_one('p.prod_name a')['href']
                image_url = "https:" + container.select_one('div.thumb_image a img')['src']
                additional_info = clean_text(container.select_one('div.spec_list').text)
                registration_date = clean_text(container.select_one('dl.meta_item.mt_date dd').text)
                rating = clean_text(container.select_one('span.text__score').text) if container.select_one('span.text__score') else "N/A"
                review_count = clean_text(container.select_one('span.text__number').text) if container.select_one('span.text__number') else "0"

                data.append([product_name, price, image_url, additional_info, link, registration_date, rating, review_count])

            except Exception as e:
                st.write(f"Error processing product: {e}")

    df = pd.DataFrame(data, columns=['상품명', '가격', '이미지 URL', '추가 정보', '상품 링크', '등록월', '평점', '리뷰 수'])
    return df

# 다운로드 링크를 생성하는 함수
def get_table_download_link(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="danawa_crawling_results.csv">Download CSV File</a>'
    return href

# Streamlit UI 설정
st.title("다나와 LED 다운라이트 크롤링")
search_query = st.text_input("검색어를 입력하세요:", "led 다운라이트")

if st.button("데이터 크롤링 시작"):
    if search_query:
        with st.spinner('크롤링 중...'):
            df = main(search_query)
        st.success("크롤링이 완료되었습니다.")
        st.dataframe(df)
        st.markdown(get_table_download_link(df), unsafe_allow_html=True)
    else:
        st.error("검색어를 입력하세요.")
