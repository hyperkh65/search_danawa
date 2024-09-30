import streamlit as st
import requests
from bs4 import BeautifulSoup

# 제품 정보 크롤링 함수
def crawl_product_info(search_query):
    base_url = "https://prod.danawa.com/list/"
    params = {'search': search_query}
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # 크롤링한 제품 정보 목록
    product_list = []
    
    # 페이지 처리
    current_page = 1
    while True:
        response = requests.get(base_url, headers=headers, params=params)
        if response.status_code != 200:
            st.error("페이지를 불러오는 데 실패했습니다.")
            break
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 제품 정보 추출
        products = soup.select('div.prod_main_info')
        for product in products:
            try:
                prod_name = product.select_one('div.prod_info > p.prod_name > a').text.strip()
                price = product.select_one('div.prod_pricelist > ul > li > p.price_sect > a > strong').text.strip()
                image = product.select_one('div.thumb_image > a > img')['src']
                link = product.select_one('div.thumb_image > a')['href']
                add_info = product.select_one('div.spec_list').text.strip()
                reg_date = product.select_one('div.prod_sub_meta > dl.meta_item.mt_date > dd').text.strip()
                rating = product.select_one('div.star-single > span.text__score').text.strip()
                review_count = product.select_one('div.text__review > span.text__number').text.strip()

                # 제품명에서 업체명 추출 (첫 번째 공백 전까지)
                company_name, prod_name = prod_name.split(' ', 1)

                product_info = {
                    '업체명': company_name,
                    '제품명': prod_name,
                    '추가 정보': add_info,
                    '가격': price,
                    '이미지': image,
                    '링크': link,
                    '평점': rating,
                    '리뷰 수': review_count,
                    '등록월': reg_date,
                }

                product_list.append(product_info)
            except Exception as e:
                st.error(f"제품 정보를 처리하는 중 오류가 발생했습니다: {e}")
                continue

        # 다음 페이지 존재 여부 확인 (data-page 값을 사용하지 않음)
        next_page = soup.select_one('a.snum.next')
        if next_page:
            current_page += 1
            params['page'] = current_page  # 다음 페이지 요청
        else:
            break

    return product_list

# Streamlit 인터페이스
st.title("다나와 제품 검색")
search_query = st.text_input("검색어를 입력하세요", value="LED 다운라이트")

if st.button("검색"):
    st.write("검색 중입니다...")
    product_list = crawl_product_info(search_query)

    if product_list:
        st.success(f"총 {len(product_list)}개의 제품을 찾았습니다.")
        
        # 제품 리스트 출력
        for product in product_list:
            image_url = product['이미지']
            
            # URL이 //로 시작할 경우 https를 추가하여 절대 경로로 변환
            if image_url.startswith("//"):
                image_url = "https:" + image_url
            elif not image_url.startswith("http"):
                st.warning(f"잘못된 이미지 URL: {image_url}")
                continue  # URL이 유효하지 않으면 건너뜀

            # 제품 정보를 표로 출력
            st.write(f"**업체명**: {product['업체명']}")
            st.write(f"**제품명**: {product['제품명']}")
            st.write(f"**추가 정보**: {product['추가 정보']}")
            st.write(f"**가격**: {product['가격']}")
            
            # 이미지 출력 (크기 조정)
            try:
                st.image(image_url, caption=product['제품명'], width=400)  # 이미지 크기 조정
            except Exception as e:
                st.error(f"이미지를 로드하는 데 오류가 발생했습니다: {e}")
            
            # 링크 출력
            product_link = f"[제품 페이지로 이동]({product['링크']})"
            st.markdown(product_link, unsafe_allow_html=True)
            
            st.write(f"**평점**: {product['평점']}")
            st.write(f"**리뷰 수**: {product['리뷰 수']}")
            st.write(f"**등록월**: {product['등록월']}")
            st.write("---")
