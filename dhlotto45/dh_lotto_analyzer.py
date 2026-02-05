"""동행복권 로또 분석 및 통계 모듈"""

import logging
from dataclasses import dataclass
from typing import List, Dict, Optional
from collections import Counter

from dh_lottery_client import DhLotteryClient, DhLotteryError
from dh_lotto_645 import DhLotto645

_LOGGER = logging.getLogger(__name__)


class DhLottoAnalyzerError(DhLotteryError):
    """로또 분석 예외 클래스입니다."""


@dataclass
class NumberFrequency:
    """번호별 출현 빈도 데이터"""
    number: int
    count: int
    percentage: float


@dataclass
class PurchaseStatistics:
    """구매 통계 데이터"""
    total_purchase_count: int  # 총 구매 횟수
    total_purchase_amount: int  # 총 구매 금액
    total_winning_count: int  # 총 당첨 횟수
    total_winning_amount: int  # 총 당첨 금액
    win_rate: float  # 당첨률
    roi: float  # 수익률 (return on investment)
    rank_distribution: Dict[int, int]  # 등수별 당첨 횟수


@dataclass
class HotColdNumbers:
    """Hot & Cold 번호 분석"""
    hot_numbers: List[int]  # 최근 자주 나온 번호 (상위 10개)
    cold_numbers: List[int]  # 최근 잘 안 나온 번호 (하위 10개)
    most_frequent: List[NumberFrequency]  # 전체 기간 최다 출현 번호


class DhLottoAnalyzer:
    """동행복권 로또 분석 클래스"""

    def __init__(self, client: DhLotteryClient):
        """DhLottoAnalyzer 클래스를 초기화합니다."""
        self.client = client
        self.lotto_645 = DhLotto645(client)

    async def async_analyze_number_frequency(
        self, recent_rounds: int = 50
    ) -> List[NumberFrequency]:
        """
        최근 N회차의 당첨번호를 분석하여 번호별 출현 빈도를 계산합니다.
        
        Args:
            recent_rounds: 분석할 최근 회차 수 (기본 50회)
            
        Returns:
            번호별 출현 빈도 리스트 (출현 횟수 내림차순)
        """
        try:
            # 최신 회차 번호 조회
            latest_round_no = await self.lotto_645.async_get_latest_round_no()
            
            # 번호 수집
            all_numbers = []
            for round_no in range(
                max(1, latest_round_no - recent_rounds + 1), latest_round_no + 1
            ):
                try:
                    winning_data = await self.lotto_645.async_get_round_info(round_no)
                    all_numbers.extend(winning_data.numbers)
                    # 보너스 번호는 제외
                except Exception as ex:
                    _LOGGER.warning(f"회차 {round_no} 조회 실패: {ex}")
                    continue

            # 빈도 계산
            total_draws = len(all_numbers) / 6  # 총 추첨 횟수
            number_counts = Counter(all_numbers)
            
            frequencies = []
            for number in range(1, 46):
                count = number_counts.get(number, 0)
                percentage = (count / total_draws * 100) if total_draws > 0 else 0
                frequencies.append(
                    NumberFrequency(
                        number=number, count=count, percentage=round(percentage, 2)
                    )
                )
            
            # 출현 횟수로 내림차순 정렬
            frequencies.sort(key=lambda x: x.count, reverse=True)
            return frequencies

        except Exception as ex:
            raise DhLottoAnalyzerError(f"번호 빈도 분석 실패: {ex}") from ex

    async def async_get_hot_cold_numbers(
        self, recent_rounds: int = 20
    ) -> HotColdNumbers:
        """
        Hot & Cold 번호를 분석합니다.
        
        Args:
            recent_rounds: 최근 분석 회차 (기본 20회)
            
        Returns:
            Hot & Cold 번호 분석 결과
        """
        try:
            # 전체 빈도 분석 (50회차)
            all_frequency = await self.async_analyze_number_frequency(50)
            
            # 최근 빈도 분석
            recent_frequency = await self.async_analyze_number_frequency(recent_rounds)
            
            # Hot numbers (최근 자주 나온 상위 10개)
            hot_numbers = [f.number for f in recent_frequency[:10]]
            
            # Cold numbers (최근 안 나온 하위 10개)
            cold_numbers = [f.number for f in recent_frequency[-10:]]
            
            # 전체 기간 최다 출현 번호 (상위 10개)
            most_frequent = all_frequency[:10]
            
            return HotColdNumbers(
                hot_numbers=hot_numbers,
                cold_numbers=cold_numbers,
                most_frequent=most_frequent,
            )

        except Exception as ex:
            raise DhLottoAnalyzerError(f"Hot/Cold 번호 분석 실패: {ex}") from ex

    async def async_get_purchase_statistics(
        self, days: int = 365
    ) -> PurchaseStatistics:
        """
        사용자의 구매 통계를 분석합니다.
        
        Args:
            days: 분석할 기간 (기본 365일)
            
        Returns:
            구매 통계 데이터
        """
        try:
            import datetime

            # 구매 내역 조회
            end_date = datetime.datetime.now()
            start_date = end_date - datetime.timedelta(days=days)
            
            result = await self.client.async_get_with_login(
                "mypage/selectMyLotteryledger.do",
                params={
                    "srchStrDt": start_date.strftime("%Y%m%d"),
                    "srchEndDt": end_date.strftime("%Y%m%d"),
                    "ltGdsCd": "LO40",  # 로또 6/45
                    "pageNum": 1,
                    "recordCountPerPage": 1000,
                    "_": int(datetime.datetime.now().timestamp() * 1000),
                },
            )
            
            items = result.get("list", [])
            
            # 통계 계산
            total_purchase_count = 0
            total_winning_count = 0
            total_winning_amount = 0
            rank_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            
            for item in items:
                quantity = item.get("prchsQty", 0)
                total_purchase_count += quantity
                
                winning_amount = item.get("ltWnAmt", 0)
                if winning_amount > 0:
                    total_winning_count += 1
                    total_winning_amount += winning_amount
                    
                    # 등수 파악 (금액 기준 추정)
                    if winning_amount >= 1000000000:  # 1등: 10억 이상
                        rank_distribution[1] += 1
                    elif winning_amount >= 10000000:  # 2등: 1천만 이상
                        rank_distribution[2] += 1
                    elif winning_amount >= 1000000:  # 3등: 100만 이상
                        rank_distribution[3] += 1
                    elif winning_amount >= 50000:  # 4등: 5만 이상
                        rank_distribution[4] += 1
                    else:  # 5등: 5천원
                        rank_distribution[5] += 1
            
            total_purchase_amount = total_purchase_count * 1000
            win_rate = (
                (total_winning_count / total_purchase_count * 100)
                if total_purchase_count > 0
                else 0
            )
            roi = (
                ((total_winning_amount - total_purchase_amount) / total_purchase_amount * 100)
                if total_purchase_amount > 0
                else 0
            )
            
            return PurchaseStatistics(
                total_purchase_count=total_purchase_count,
                total_purchase_amount=total_purchase_amount,
                total_winning_count=total_winning_count,
                total_winning_amount=total_winning_amount,
                win_rate=round(win_rate, 2),
                roi=round(roi, 2),
                rank_distribution=rank_distribution,
            )

        except Exception as ex:
            raise DhLottoAnalyzerError(f"구매 통계 분석 실패: {ex}") from ex

    @staticmethod
    def generate_random_numbers(count: int = 6) -> List[int]:
        """
        중복 없는 랜덤 로또 번호를 생성합니다.
        
        Args:
            count: 생성할 번호 개수 (기본 6개)
            
        Returns:
            정렬된 랜덤 번호 리스트
        """
        import random
        
        if count < 1 or count > 45:
            raise ValueError("번호 개수는 1~45 사이여야 합니다.")
        
        numbers = random.sample(range(1, 46), count)
        return sorted(numbers)

    async def async_check_winning(
        self, my_numbers: List[int], round_no: Optional[int] = None
    ) -> Dict[str, any]:
        """
        내 번호가 당첨되었는지 확인합니다.
        
        Args:
            my_numbers: 내가 선택한 번호 (6개)
            round_no: 확인할 회차 (None이면 최신 회차)
            
        Returns:
            당첨 결과 (등수, 일치 개수, 보너스 일치 여부 등)
        """
        try:
            if len(my_numbers) != 6:
                raise ValueError("번호는 정확히 6개여야 합니다.")
            
            # 회차 정보 조회
            if round_no is None:
                round_no = await self.lotto_645.async_get_latest_round_no()
            
            winning_data = await self.lotto_645.async_get_round_info(round_no)
            
            # 일치 개수 계산
            matching_count = len(set(my_numbers) & set(winning_data.numbers))
            bonus_match = winning_data.bonus_num in my_numbers
            
            # 등수 결정
            rank = 0
            if matching_count == 6:
                rank = 1
            elif matching_count == 5 and bonus_match:
                rank = 2
            elif matching_count == 5:
                rank = 3
            elif matching_count == 4:
                rank = 4
            elif matching_count == 3:
                rank = 5
            
            return {
                "round_no": round_no,
                "my_numbers": sorted(my_numbers),
                "winning_numbers": winning_data.numbers,
                "bonus_number": winning_data.bonus_num,
                "matching_count": matching_count,
                "bonus_match": bonus_match,
                "rank": rank,
                "is_winner": rank > 0,
            }

        except Exception as ex:
            raise DhLottoAnalyzerError(f"당첨 확인 실패: {ex}") from ex
