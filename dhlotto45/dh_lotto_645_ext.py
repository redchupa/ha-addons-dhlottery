"""
Lotto 6/45 Public API Extension
Provides winning details using public API
"""

import logging
from dataclasses import dataclass
from typing import Optional
import aiohttp

_LOGGER = logging.getLogger(__name__)

PUBLIC_API_URL = "https://www.dhlottery.co.kr/common.do"


@dataclass
class Lotto645WinningDetails:
    """Lotto 6/45 winning details from public API"""
    round_no: int
    draw_date: str
    # Winning numbers
    numbers: list[int]
    bonus_num: int
    # Sales
    total_sales: int  # Total sales amount (totSellamnt)
    # 1st prize
    first_prize_amount: int  # 1st prize per winner (firstWinamnt)
    first_prize_winners: int  # Number of 1st prize winners (firstPrzwnerCo)
    first_prize_total: int  # Total 1st prize amount (firstAccumamnt)
    # Additional prizes (if available in response)
    second_prize_amount: Optional[int] = None
    second_prize_winners: Optional[int] = None
    third_prize_amount: Optional[int] = None
    third_prize_winners: Optional[int] = None
    fourth_prize_amount: Optional[int] = None
    fourth_prize_winners: Optional[int] = None
    fifth_prize_amount: Optional[int] = None
    fifth_prize_winners: Optional[int] = None


async def get_lotto645_winning_details(round_no: Optional[int] = None) -> Lotto645WinningDetails:
    """
    Get Lotto 6/45 winning details from public API
    
    Args:
        round_no: Round number (None for latest)
        
    Returns:
        Lotto645WinningDetails object
        
    Example response:
    {
        "totSellamnt": 111840714000,
        "returnValue": "success",
        "drwNoDate": "2024-05-11",
        "firstWinamnt": 1396028764,
        "firstPrzwnerCo": 19,
        "firstAccumamnt": 26524546516,
        "drwNo": 1119,
        "drwtNo1": 1, "drwtNo2": 9, "drwtNo3": 12,
        "drwtNo4": 13, "drwtNo5": 20, "drwtNo6": 45,
        "bnusNo": 3
    }
    """
    params = {"method": "getLottoNumber"}
    if round_no:
        params["drwNo"] = round_no
    
    try:
        # Use proper headers to avoid redirects
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Referer": "https://www.dhlottery.co.kr/",
        }
        
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
            async with session.get(PUBLIC_API_URL, params=params, allow_redirects=False) as resp:
                _LOGGER.debug(f"Lotto 645 ext API response: {resp.status}, URL: {resp.url}")
                
                if resp.status != 200:
                    raise Exception(f"API request failed: {resp.status}")
                
                # Check content type
                content_type = resp.headers.get('Content-Type', '')
                if 'application/json' not in content_type and 'text/javascript' not in content_type:
                    text = await resp.text()
                    _LOGGER.error(f"Unexpected content type: {content_type}, response: {text[:200]}")
                    raise Exception(f"API returned non-JSON response (Content-Type: {content_type})")
                
                data = await resp.json()
                
                if data.get("returnValue") != "success":
                    raise Exception(f"API returned error: {data}")
                
                # Parse response
                return Lotto645WinningDetails(
                    round_no=data["drwNo"],
                    draw_date=data["drwNoDate"],
                    numbers=[
                        data["drwtNo1"],
                        data["drwtNo2"],
                        data["drwtNo3"],
                        data["drwtNo4"],
                        data["drwtNo5"],
                        data["drwtNo6"],
                    ],
                    bonus_num=data["bnusNo"],
                    total_sales=data["totSellamnt"],
                    first_prize_amount=data["firstWinamnt"],
                    first_prize_winners=data["firstPrzwnerCo"],
                    first_prize_total=data["firstAccumamnt"],
                )
    
    except Exception as ex:
        _LOGGER.error(f"Failed to get lotto645 winning details: {ex}")
        raise
