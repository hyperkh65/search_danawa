import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re
import base64

def get_page_content(search_query, page_num):
    url = f"https://search.danawa.com/dsearch.php?query={search_query}&page={page_num}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    return BeautifulSoup(response.content, 'html.parser')

def clean_text(text):
    return re.sub(r'\s+', ' ', text).strip()

def main(search_query, start_page, end_page):
    data = []

    for page_num in range(start_page, end_page + 1):
        soup = get_page_content(search_query, page_num)
        product_containers = soup.select('div.prod_main_info')

        for container in product_containers:
            try:
                product_name = clean_text(container.select_one('p.prod_name').text)
                price = clean_text(container.select_one('p.price_sect').text)
                link = container.select_one('a')['href']
                image_url = container.select_one('img')['src']
                additional_info = clean_text(container.select_one('p.spec_list').text)
                registration_date = datetime.today().strftime('%Y-%m-%d')
                rating = clean_text(container.select_one('span.rating').text) if container.select_one('span.rating') else "N/A"
                review_count = clean_text(container.select_one('span.cm_count').text) if container.select_one('span.cm_count') else "0"

                data.append([product_name, price, image_url, additional_info, link, registration_date, rating, review_count])

            except Exception as e:
                st.write(f"Error processing product: {e}")

    df = pd.DataFrame(data, columns=['상품', '가격', '이미지 URL', '부가정보', '링크', '등록월', '평점', '리뷰 수'])
    return df

def get_table_download_link(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="danawa_crawling_results.csv">Download CSV File</a>'
    return href

# Streamlit UI 설정
st.title("다나와 웹 크롤링")
search_query = st.text_input("검색어를 입력하세요:")
start_page = st.number_input("시작 페이지를 입력하세요:", min_value=1, value=1)
end_page = st.number_input("종료 페이지를 입력하세요:", min_value=1, value=2)

if st.button("데이터 크롤링 시작"):
    if search_query:
        with st.spinner('크롤링 중...'):
            df = main(search_query, start_page, end_page)
        st.success("크롤링이 완료되었습니다.")
        st.dataframe(df)
        st.markdown(get_table_download_link(df), unsafe_allow_html=True)
    else:
        st.error("검색어를 입력하세요.")
