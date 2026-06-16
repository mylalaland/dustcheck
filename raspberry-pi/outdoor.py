"""
양산 지역 실외 미세먼지(PM2.5/PM10) 조회 모듈
에어코리아 Open API (data.go.kr)를 사용합니다.

API 키 발급: https://www.data.go.kr/data/15073861/openapi.do
"""

import logging
import time
import urllib.request
import urllib.parse
import json

logger = logging.getLogger(__name__)

# 캐시: 에어코리아 데이터는 매시 정각에 갱신되므로 1시간 캐시
_cache = {"pm25": None, "pm10": None, "timestamp": 0, "station": ""}
CACHE_TTL = 3600  # 1시간 (초)


def fetch_outdoor_data(api_key, station_name="물금읍"):
    """
    에어코리아 API에서 실외 PM2.5, PM10 값을 가져옵니다.

    Returns:
        dict: {"pm25": float|None, "pm10": float|None}
    """
    now = time.time()

    # 캐시 확인
    if _cache["pm25"] is not None and (now - _cache["timestamp"]) < CACHE_TTL:
        return {"pm25": _cache["pm25"], "pm10": _cache["pm10"]}

    if not api_key:
        logger.debug("에어코리아 API 키가 설정되지 않았습니다.")
        return {"pm25": _cache["pm25"], "pm10": _cache["pm10"]}

    try:
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

        items = data.get("response", {}).get("body", {}).get("items", [])
        if not items:
            logger.warning(f"에어코리아 API: '{station_name}' 측정소 데이터 없음")
            return {"pm25": _cache["pm25"], "pm10": _cache["pm10"]}

        item = items[0]
        pm25_str = item.get("pm25Value", "")
        pm10_str = item.get("pm10Value", "")

        pm25 = float(pm25_str) if pm25_str and pm25_str != "-" else _cache["pm25"]
        pm10 = float(pm10_str) if pm10_str and pm10_str != "-" else _cache["pm10"]

        _cache["pm25"] = pm25
        _cache["pm10"] = pm10
        _cache["timestamp"] = now
        _cache["station"] = station_name
        logger.info(f"실외 ({station_name}): PM2.5={pm25}, PM10={pm10} μg/m³")
        return {"pm25": pm25, "pm10": pm10}

    except Exception as e:
        logger.error(f"실외 미세먼지 조회 실패: {e}")
        return {"pm25": _cache["pm25"], "pm10": _cache["pm10"]}


def fetch_outdoor_pm25(api_key, station_name="물금읍"):
    """하위 호환용 래퍼"""
    result = fetch_outdoor_data(api_key, station_name)
    return result["pm25"]
