import requests
import os
from datetime import datetime
from dotenv import load_dotenv
from googletrans import Translator

# .env 파일 로드
load_dotenv()

class FlightFinder:
    def __init__(self):
        self.amadeus_api_key = os.getenv("AMADEUS_API_KEY")
        self.amadeus_api_secret = os.getenv("AMADEUS_API_SECRET")
        self.amadeus_token = self._get_amadeus_token()
        self.translator = Translator()

    def _get_amadeus_token(self):
        """항공 데이터 접근을 위한 토큰 발급"""
        url = "https://test.api.amadeus.com/v1/security/oauth2/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": self.amadeus_api_key,
            "client_secret": self.amadeus_api_secret
        }
        try:
            response = requests.post(url, data=data)
            return response.json().get("access_token")
        except Exception as e:
            print(f"❌ 토큰 발급 실패: {e}")
            return None

    def get_airport_code(self, city_name):
        """도시명을 공항 코드로 변환"""
        try:
            # 한글 -> 영어 번역
            translated = self.translator.translate(city_name, src='ko', dest='en')
            english_city = translated.text
            print(f"🔍 검색어 변환: {city_name} -> {english_city}")
        except:
            english_city = city_name

        url = "https://test.api.amadeus.com/v1/reference-data/locations"
        headers = {"Authorization": f"Bearer {self.amadeus_token}"}
        params = {
            "subType": "CITY",
            "keyword": english_city.upper(),
            "page[limit]": 1
        }
        
        res = requests.get(url, headers=headers, params=params)
        
        # API 응답이 성공(200)이 아닐 경우 이유 출력
        if res.status_code != 200:
            print(f"⚠️ API 응답 에러 (코드: {res.status_code})")
            print(f"내용: {res.text}") # 에러 메시지를 직접 확인하기 위함
            return None

        data = res.json()
        if data.get('data') and len(data['data']) > 0:
            return data['data'][0]['iataCode']
        return None

    def get_flights(self, origin, destination, date):
        """최저가 항공권 조회"""
        url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
        headers = {"Authorization": f"Bearer {self.amadeus_token}"}
        params = {
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": date,
            "adults": 1,
            "currencyCode": "KRW",
            "max": 1
        }
        res = requests.get(url, headers=headers, params=params)
        if res.status_code == 200:
            data = res.json()
            if data.get('data'):
                offer = data['data'][0]
                return {
                    "price": offer['price']['total'],
                    "airline": offer['itineraries'][0]['segments'][0]['carrierCode']
                }
        return None

def main():
    finder = FlightFinder()
    
    if not finder.amadeus_token:
        print("❌ API 토큰을 가져오지 못했습니다. .env 파일의 키를 확인하세요.")
        return

    print("\n✈️  실시간 최저가 항공권 검색기")
    print("-" * 30)
    
    target_city = input("어디로 가고 싶으신가요? (한글 또는 영문): ")
    date = input("출발 날짜를 입력하세요 (YYYY-MM-DD): ")
    
    dest_code = finder.get_airport_code(target_city)
    
    if not dest_code:
        print(f"❌ '{target_city}'에 대한 공항 정보를 찾을 수 없습니다.")
        return

    print(f"🎫 {dest_code}행 최저가 항공권을 조회 중...")
    flight = finder.get_flights("ICN", dest_code, date)
    
    if flight:
        print(f"\n✅ 검색 완료!")
        print(f"📍 목적지: {target_city} ({dest_code})")
        print(f"💰 최저가: {float(flight['price']):,.0f} KRW")
        print(f"✈️  항공사: {flight['airline']}")
    else:
        print("\n😭 해당 날짜에는 항공권 데이터가 없습니다.")

if __name__ == "__main__":
    main()