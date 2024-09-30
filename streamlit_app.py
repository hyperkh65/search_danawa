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

# 최대 페이지 수를 가져오는 함수
def get_total_pages(soup):
    paging_div = soup.select_one('div.paging_number_wrap')
    if paging_div:
        pages = paging_div.find_all('a', class_='snum')
        return int(pages[-1].get('data-page')) if pages else 1
    return 1

# 제품 정보 크롤링 함수
def crawl_product_info(search_query):
    product_list = []
    soup = get_page_content(search_query, 1)
    max_pages = get_total_pages(soup)
    
    if max_pages == 0:
        st.warning("페이지를 찾을 수 없습니다.")
        return product_list

    with st.progress(0) as progress_bar:
        for page_num in range(1, max_pages + 1):
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

                    # 이미지 URL 가져오기
                    image_tag = product.select_one('div.thumb_image a img')
                    image_url = image_tag['src'] if image_tag else '정보 없음'

                    # 링크 가져오기
                    link_tag = product.select_one('div.thumb_image a')
                    link = link_tag['href'] if link_tag else '정보 없음'

                    # 추가 정보 가져오기
                    spec_tag = product.select_one('div.spec_list')
                    additional_info = spec_tag.text.strip() if spec_tag else '정보 없음'

                    # 등록월 가져오기
                    date_tag = product.select_one('div.prod_sub_meta dl.meta_item.mt_date dd')
                    date = date_tag.text.strip() if date_tag else '정보 없음'

                    # 평점 가져오기
                    rating_tag = product.select_one('div.star-single span.text__score')
                    rating = rating_tag.text.strip() if rating_tag else '정보 없음'

                    # 리뷰 수 가져오기
                    review_count_tag = product.select_one('div.text__review span.text__number')
                    review_count = review_count_tag.text.strip() if review_count_tag else '정보 없음'

                    # 데이터 저장
                    product_list.append({
                        '제품명': name,
                        '가격': price,
                        '이미지 URL': image_url,
                        '링크': link,
                        '추가 정보': additional_info,
                        '등록월': date,
                        '평점': rating,
                        '리뷰 수': review_count
                    })

                except Exception as e:
                    print(f"Error processing product: {e}")

            # 진행률 업데이트
            progress_bar.progress((page_num / max_pages) if max_pages > 0 else 0)

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
    if product_list:
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
    else:
        st.warning("검색 결과가 없습니다.")
