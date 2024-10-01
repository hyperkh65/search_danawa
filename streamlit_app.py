import streamlit as st
import requests
from bs4 import BeautifulSoup
import time  # for simulating progress

# 페이지 컨텐츠를 받아오는 함수
def get_page_content(search_query, page_num):
    url = f"https://search.danawa.com/dsearch.php?query={search_query}&page={page_num}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    return BeautifulSoup(response.content, 'html.parser')

# 검색 결과를 처리하는 함수
def process_results(soup):
    products = []
    product_items = soup.select('.prod_main_info')
    for item in product_items:
        name_tag = item.select_one('.prod_name a')
        price_tag = item.select_one('.price_sect a strong')

        # 각 태그가 존재하는지 체크하고 추가
        if name_tag and price_tag:
            name = name_tag.text.strip()
            price = price_tag.text.strip()
            link = name_tag['href']
            products.append({'상품명': name, '가격': price, '링크': link})

    return products

# Streamlit 레이아웃 설정
st.set_page_config(layout="wide")

# 왼쪽에 검색 옵션 창 만들기
with st.sidebar:
    st.title("옵션 창")
    search_query = st.text_input("검색어를 입력하세요", "")
    search_button = st.button("검색")

# 오른쪽에 검색 결과 표시
if search_button and search_query:
    st.title("검색 결과")

    # 진행률 표시할 프로그레스 바 추가
    progress_bar = st.progress(0)
    results = []

    # 총 10페이지까지 검색한다고 가정하고 진행 상황 표시
    for i in range(1, 11):
        progress_bar.progress(i * 10)  # 진행률 업데이트
        st.write(f"{i}/10 페이지 크롤링 중...")
        soup = get_page_content(search_query, i)
        results += process_results(soup)
        time.sleep(1)  # 크롤링 속도를 조절하기 위한 딜레이

    # 결과를 테이블로 표시
    if results:
        st.write("검색 완료!")
        df = pd.DataFrame(results)
        st.dataframe(df)
    else:
        st.write("검색 결과가 없습니다.")
