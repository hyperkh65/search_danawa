import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from openpyxl import Workbook
from openpyxl.drawing.image import Image as ExcelImage
import io

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
    
    # 페이지 수 자동 계산
    soup = get_page_content(search_query, 1)
    paging_div = soup.select_one('div.paging_number_wrap')

    if paging_div:
        max_pages = int(paging_div.find_all('a')[-1]['data-page'])
    else:
        st.error("페이지 정보를 가져올 수 없습니다. 검색어를 확인해 주세요.")
        return []  # 빈 리스트 반환하여 이후 코드를 중단

    # 각 페이지에서 제품 정보 크롤링
    for page_num in range(1, max_pages + 1):
        st.session_state.progress_bar.progress(page_num / max_pages)  # 진행률 표시
        soup = get_page_content(search_query, page_num)
        products = soup.select('li.prod_item')

        for product in products:
            try:
                # 업체명과 제품명 가져오기
                name_tag = product.select_one('p.prod_name a')
                full_name = name_tag.text.strip() if name_tag else '정보 없음'
                업체명 = full_name.split()[0]  # 공백 전까지 업체명 추출
                제품명 = ' '.join(full_name.split()[1:])  # 첫 공백 이후 제품명 추출

                # 가격 가져오기
                price_tag = product.select_one('p.price_sect a strong')
                가격 = price_tag.text.strip() if price_tag else '정보 없음'

                # 이미지 URL 가져오기
                img_tag = product.select_one('div.thumb_image a img')
                이미지_URL = img_tag['src'] if img_tag else '정보 없음'

                # 링크 가져오기
                link_tag = product.select_one('div.thumb_image a')
                링크 = link_tag['href'] if link_tag else '정보 없음'

                # 추가 정보 가져오기
                추가정보_tag = product.select_one('div.spec_list')
                추가정보 = 추가정보_tag.text.strip() if 추가정보_tag else '정보 없음'

                # 등록월 가져오기
                등록월_tag = product.select_one('div.prod_sub_meta dl.meta_item.mt_date dd')
                등록월 = 등록월_tag.text.strip() if 등록월_tag else '정보 없음'

                # 평점 가져오기
                평점_tag = product.select_one('div.star-single span.text__score')
                평점 = 평점_tag.text.strip() if 평점_tag else '정보 없음'

                # 리뷰 수 가져오기
                리뷰수_tag = product.select_one('div.text__review span.text__number')
                리뷰수 = 리뷰수_tag.text.strip() if 리뷰수_tag else '정보 없음'

                # 데이터 저장
                product_list.append({
                    '업체명': 업체명,
                    '제품명': 제품명,
                    '추가정보': 추가정보,
                    '가격': 가격,
                    '이미지': 이미지_URL,
                    '링크': 링크,
                    '평점': 평점,
                    '리뷰수': 리뷰수,
                    '등록월': 등록월
                })

            except Exception as e:
                print(f"Error processing product: {e}")

    return product_list

# 엑셀 파일 생성 함수
def create_excel_with_images(product_list):
    wb = Workbook()
    ws = wb.active
    ws.title = "제품 목록"
    
    # 헤더 추가
    headers = ['업체명', '제품명', '추가정보', '가격', '이미지', '링크', '평점', '리뷰수', '등록월']
    ws.append(headers)

    for product in product_list:
        # 제품 정보 추가
        row = [
            product['업체명'],
            product['제품명'],
            product['추가정보'],
            product['가격'],
            product['링크'],
            product['평점'],
            product['리뷰수'],
            product['등록월']
        ]
        ws.append(row)
        
        # 이미지 추가
        if product['이미지'] != '정보 없음':
            image_response = requests.get(product['이미지'])
            img = ExcelImage(io.BytesIO(image_response.content))
            img.width = 100  # 이미지 너비 조정 (원하는 대로 설정 가능)
            img.height = 100  # 이미지 높이 조정 (원하는 대로 설정 가능)
            ws.add_image(img, f'E{ws.max_row}')  # E열에 이미지 삽입

    return wb

# Streamlit 애플리케이션 설정
st.set_page_config(layout="wide")

# 왼쪽 옵션 패널 만들기
with st.sidebar:
    st.title("검색 옵션")
    search_query = st.text_input("검색어 입력", "노트북")
    search_button = st.button("검색")
    # 진행률 바 초기화
    if 'progress_bar' not in st.session_state:
        st.session_state.progress_bar = st.progress(0)

# 검색 버튼이 눌렸을 때
if search_button:
    if not search_query.strip():
        st.error("검색어를 입력해 주세요.")
    else:
        st.write(f"'{search_query}' 검색 결과:")
        
        # 크롤링 시작
        product_list = crawl_product_info(search_query)
        
        if not product_list:
            st.warning("제품이 없습니다. 다른 검색어로 시도해 주세요.")
        else:
            # 결과를 데이터프레임으로 변환 후 출력
            df = pd.DataFrame(product_list)
            st.dataframe(df)

            # 엑셀 파일 생성
            wb = create_excel_with_images(product_list)
            excel_buffer = io.BytesIO()
            wb.save(excel_buffer)
            excel_buffer.seek(0)

            # 엑셀 파일 다운로드 버튼
            st.download_button(
                label="엑셀 다운로드",
                data=excel_buffer,
                file_name=f'{search_query}_검색결과.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
