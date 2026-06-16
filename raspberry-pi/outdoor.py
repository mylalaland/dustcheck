"""
양산 지역 실외 미세먼지(PM2.5) 조회 모듈
에어코리아 Open API (data.go.kr)를 사용합니다.

API 키 발급: https://www.data.go.kr/data/15073861/openapi.do
"""

import logging
import time
import urllib.request
import urllib.parse
import json

logger = logging.getLogger(__name__)

# 캐시: 30분마다 갱신
_cache = {"pm25": None, "timestamp": 0, "station": ""}
CACHE_TTL = 1800  # 30분 (초)


def fetch_outdoor_pm25(api_key, station_name="물금읍"):
    """
    에어코리아 API에서 실외 PM2.5 값을 가져옵니다.
    30분 캐시를 사용하여 불필요한 API 호출을 방지합니다.

    Args:
        api_key: data.go.kr에서 발급받은 API 키 (인코딩된 키)
        station_name: 측정소 이름 (기본: 물금읍)

    Returns:
        float or None: PM2.5 값 (μg/m³), 실패 시 None
    """
    now = time.time()

    # 캐시 확인
    if _cache["pm25"] is not None and (now - _cache["timestamp"]) < CACHE_TTL:
        return _cache["pm25"]

    if not api_key:
        logger.debug("에어코리아 API 키가 설정되지 않았습니다.")
        return None

    try:
        # API URL 구성
        base_url = "http://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getMsrstnAcctoRltmMesureDnsty"
        params = {
            "serviceKey": api_key,
            "returnType": "json",
            "numOfRows": "1",
            "pageNo": "1",
            "stationName": station_name,
            "dataTerm": "DAILY",
            "ver": "1.0",
        }

        url = base_url + "?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
        req = urllib.request.Request(url)
        req.add_header("Accept", "application/json")

        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        # 응답 파싱
        items = data.get("response", {}).get("body", {}).get("items", [])
        if not items:
            logger.warning(f"에어코리아 API: '{station_name}' 측정소 데이터 없음")
            return _cache["pm25"]  # 이전 캐시 반환

        item = items[0]
        pm25_str = item.get("pm25Value", "")

        if pm25_str and pm25_str != "-":
            pm25 = float(pm25_str)
            _cache["pm25"] = pm25
            _cache["timestamp"] = now
            _cache["station"] = station_name
            logger.info(f"실외 PM2.5 ({station_name}): {pm25} μg/m³")
            return pm25
        else:
            logger.warning(f"에어코리아 API: PM2.5 값 없음 (raw: '{pm25_str}')")
            return _cache["pm25"]

    except Exception as e:
        logger.error(f"실외 PM2.5 조회 실패: {e}")
        return _cache["pm25"]  # 이전 캐시 반환
