import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd

# 페이지 컨텐츠를 받아오는 함수
def get_page_content(search_query, page_num):
    url = f"https://search.danawa.com/dsearch.php?query={search_query}&page={page_num}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    return BeautifulSoup(response.content, 'html.parser')

# 최대 페이지 수를 찾는 함수
def get_max_pages(search_query):
    soup = get_page_content(search_query, 1)
    pagination = soup.select_one('div.paging_number_wrap')
    if pagination:
        return len(pagination.select('a.click_log_page'))
    return 0

# 제품 정보 크롤링 함수
def crawl_product_info(search_query):
    product_list = []
    max_pages = get_max_pages(search_query)  # 최대 페이지 수 가져오기

    for page_num in range(1, max_pages + 1):
        soup = get_page_content(search_query, page_num)
        products = soup.select('li.prod_item')

        for product in products:
            try:
                # 제품명과 업체명 가져오기
                name_tag = product.select_one('p.prod_name a')
                name = name_tag.text.strip() if name_tag else '정보 없음'
                company_name = name.split()[0] if name else '정보 없음'
                product_name = ' '.join(name.split()[1:]) if name else '정보 없음'

                # 가격 가져오기
                price_tag = product.select_one('p.price_sect a strong')
                price = price_tag.text.strip() if price_tag else '정보 없음'

                # 이미지 URL 가져오기
                image_tag = product.select_one('div.thumb_image a img')
                image_url = image_tag['src'] if image_tag else ''

                # 링크 가져오기
                link = product.select_one('div.thumb_image a')['href'] if product.select_one('div.thumb_image a') else '정보 없음'

                # 추가 정보, 등록 월, 평점, 리뷰 수 가져오기
                additional_info_tag = product.select_one('div.spec_list')
                additional_info = additional_info_tag.text.strip() if additional_info_tag else '정보 없음'

                registration_month_tag = product.select_one('div.prod_sub_meta dl.meta_item.mt_date dd')
                registration_month = registration_month_tag.text.strip() if registration_month_tag else '정보 없음'

                rating_tag = product.select_one('div.star-single span.text__score')
                rating = rating_tag.text.strip() if rating_tag else '정보 없음'

                review_count_tag = product.select_one('div.text__review span.text__number')
                review_count = review_count_tag.text.strip() if review_count_tag else '정보 없음'

                # 데이터 저장
                product_list.append({
                    '업체명': company_name,
                    '제품명': product_name,
                    '추가정보': additional_info,
                    '가격': price,
                    '이미지': image_url,
                    '링크': link,
                    '평점': rating,
                    '리뷰': review_count,
                    '등록월': registration_month
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

    # 이미지 URL을 이미지로 변환
    df['이미지'] = df['이미지'].apply(lambda x: f'<img src="{x}" width="100" />' if x else '정보 없음')

    # Streamlit에서 HTML로 이미지 표시
    st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)

    # CSV 파일 다운로드 버튼
    csv = df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="CSV 다운로드",
        data=csv,
        file_name=f'{search_query}_검색결과.csv',
        mime='text/csv'
    )
