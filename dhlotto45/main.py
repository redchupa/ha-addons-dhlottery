"""
Lotto 45 Add-on Main Application
Home Assistant Add-on for 동행복권 로또 6/45
"""

import os
import asyncio
import logging
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import uvicorn

from dh_lottery_client import DhLotteryClient
from dh_lotto_645 import DhLotto645
from dh_lotto_analyzer import DhLottoAnalyzer

# 로그 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 전역 변수
config = {
    "username": os.getenv("USERNAME", ""),
    "password": os.getenv("PASSWORD", ""),
    "enable_lotto645": os.getenv("ENABLE_LOTTO645", "true").lower() == "true",
    "update_interval": int(os.getenv("UPDATE_INTERVAL", "3600")),
    "use_mqtt": os.getenv("USE_MQTT", "true").lower() == "true",
    "ha_url": os.getenv("HA_URL", "http://supervisor/core"),
    "supervisor_token": os.getenv("SUPERVISOR_TOKEN", ""),
}

client: Optional[DhLotteryClient] = None
lotto_645: Optional[DhLotto645] = None
analyzer: Optional[DhLottoAnalyzer] = None


async def init_client():
    """클라이언트 초기화"""
    global client, lotto_645, analyzer
    
    if not config["username"] or not config["password"]:
        logger.error("Username or password not configured")
        return False
    
    try:
        logger.info("Initializing DH Lottery client...")
        client = DhLotteryClient(config["username"], config["password"])
        await client.async_login()
        
        if config["enable_lotto645"]:
            lotto_645 = DhLotto645(client)
            analyzer = DhLottoAnalyzer(client)
        
        logger.info("Client initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize client: {e}", exc_info=True)
        return False


async def cleanup_client():
    """클라이언트 정리"""
    global client
    if client and client.session:
        try:
            await client.session.close()
            logger.info("Client session closed")
        except Exception as e:
            logger.error(f"Error closing client session: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 라이프사이클 관리"""
    # Startup
    logger.info("Starting Lotto 45 Add-on...")
    logger.info(f"Configuration: username={config['username']}, "
                f"enable_lotto645={config['enable_lotto645']}, "
                f"update_interval={config['update_interval']}")
    
    # 클라이언트 초기화
    await init_client()
    
    # 백그라운드 작업 시작
    task = asyncio.create_task(background_tasks())
    
    logger.info("Add-on started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Lotto 45 Add-on...")
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    await cleanup_client()
    logger.info("Add-on shut down successfully")


# FastAPI 앱
app = FastAPI(
    title="Lotto 45",
    version="0.2.0",
    lifespan=lifespan
)


async def background_tasks():
    """백그라운드 작업"""
    # 초기 지연
    await asyncio.sleep(10)
    
    while True:
        try:
            await update_sensors()
            await asyncio.sleep(config["update_interval"])
        except asyncio.CancelledError:
            logger.info("Background task cancelled")
            break
        except Exception as e:
            logger.error(f"Background task error: {e}", exc_info=True)
            await asyncio.sleep(60)


async def update_sensors():
    """센서 업데이트"""
    if not client or not client.logged_in:
        logger.warning("Client not logged in, attempting to login...")
        try:
            await client.async_login()
        except Exception as e:
            logger.error(f"Failed to login: {e}")
            return
    
    try:
        logger.info("Updating sensors...")
        
        # 예치금 조회
        balance = await client.async_get_balance()
        await publish_sensor("lotto45_deposit", balance.deposit, {
            "purchase_available": balance.purchase_available,
            "reservation_purchase": balance.reservation_purchase,
            "withdrawal_request": balance.withdrawal_request,
            "this_month_accumulated": balance.this_month_accumulated_purchase,
            "unit_of_measurement": "원",
            "friendly_name": "로또45 예치금",
        })
        
        # 통계 업데이트 (로또 활성화 시)
        if config["enable_lotto645"] and analyzer:
            # 번호 빈도
            frequency = await analyzer.async_analyze_number_frequency(50)
            top_num = frequency[0] if frequency else None
            if top_num:
                await publish_sensor("lotto45_top_frequency_number", top_num.number, {
                    "count": top_num.count,
                    "percentage": top_num.percentage,
                    "unit_of_measurement": "회",
                    "friendly_name": "로또45 최다 출현 번호",
                })
            
            # Hot/Cold 번호
            hot_cold = await analyzer.async_get_hot_cold_numbers(20)
            await publish_sensor("lotto45_hot_numbers", 
                ",".join(map(str, hot_cold.hot_numbers)), {
                    "numbers": hot_cold.hot_numbers,
                    "friendly_name": "로또45 Hot 번호",
                })
            await publish_sensor("lotto45_cold_numbers",
                ",".join(map(str, hot_cold.cold_numbers)), {
                    "numbers": hot_cold.cold_numbers,
                    "friendly_name": "로또45 Cold 번호",
                })
            
            # 구매 통계
            stats = await analyzer.async_get_purchase_statistics(365)
            await publish_sensor("lotto45_total_winning", stats.total_winning_amount, {
                "total_purchase": stats.total_purchase_amount,
                "total_purchase_count": stats.total_purchase_count,
                "total_winning_count": stats.total_winning_count,
                "win_rate": stats.win_rate,
                "roi": stats.roi,
                "unit_of_measurement": "원",
                "friendly_name": "로또45 총 당첨금",
            })
        
        logger.info("Sensors updated successfully")
        
    except Exception as e:
        logger.error(f"Failed to update sensors: {e}", exc_info=True)


async def publish_sensor(entity_id: str, state, attributes: dict = None):
    """센서 상태 발행 (REST API 사용)"""
    import aiohttp
    
    if not config["supervisor_token"]:
        logger.debug(f"Skipping sensor publish (no token): {entity_id}")
        return
    
    url = f"{config['ha_url']}/api/states/sensor.{entity_id}"
    headers = {
        "Authorization": f"Bearer {config['supervisor_token']}",
        "Content-Type": "application/json",
    }
    data = {
        "state": state,
        "attributes": attributes or {},
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=headers, ssl=False) as resp:
                if resp.status not in [200, 201]:
                    logger.error(f"Failed to publish sensor {entity_id}: {resp.status} - {await resp.text()}")
                else:
                    logger.debug(f"Published sensor {entity_id}: {state}")
    except Exception as e:
        logger.error(f"Error publishing sensor {entity_id}: {e}")


@app.get("/", response_class=HTMLResponse)
async def root():
    """루트 페이지"""
    status_icon = "🟢" if client and client.logged_in else "🔴"
    status_text = "Connected" if client and client.logged_in else "Disconnected"
    
    return f"""
    <!DOCTYPE html>
    <html>
        <head>
            <meta charset="UTF-8">
            <title>Lotto 45</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1 {{ color: #333; }}
                .status {{ font-size: 18px; margin: 20px 0; }}
                .info {{ background: #f5f5f5; padding: 15px; border-radius: 5px; }}
                a {{ color: #0066cc; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <h1>동행복권 로또 45</h1>
            <div class="status">
                Status: {status_icon} {status_text}
            </div>
            <div class="info">
                <p><strong>Username:</strong> {config['username']}</p>
                <p><strong>Update Interval:</strong> {config['update_interval']}s</p>
                <p><strong>Lotto 645 Enabled:</strong> {config['enable_lotto645']}</p>
            </div>
            <h2>Links</h2>
            <ul>
                <li><a href="/docs">API Documentation</a></li>
                <li><a href="/health">Health Check</a></li>
                <li><a href="/stats">Statistics</a></li>
            </ul>
        </body>
    </html>
    """


@app.get("/health")
async def health():
    """헬스체크"""
    return {
        "status": "ok" if client and client.logged_in else "error",
        "logged_in": client.logged_in if client else False,
        "username": config["username"],
        "lotto645_enabled": config["enable_lotto645"],
    }


@app.post("/random")
async def generate_random(count: int = 6, games: int = 1):
    """랜덤 번호 생성"""
    if not analyzer:
        raise HTTPException(status_code=400, detail="Lotto 645 not enabled")
    
    if count < 1 or count > 45:
        raise HTTPException(status_code=400, detail="Count must be between 1 and 45")
    
    if games < 1 or games > 5:
        raise HTTPException(status_code=400, detail="Games must be between 1 and 5")
    
    results = []
    for _ in range(games):
        numbers = analyzer.generate_random_numbers(count)
        results.append(numbers)
    
    return {"numbers": results}


@app.post("/check")
async def check_winning(numbers: list[int], round_no: Optional[int] = None):
    """당첨 확인"""
    if not analyzer:
        raise HTTPException(status_code=400, detail="Lotto 645 not enabled")
    
    if len(numbers) != 6:
        raise HTTPException(status_code=400, detail="Must provide exactly 6 numbers")
    
    if any(n < 1 or n > 45 for n in numbers):
        raise HTTPException(status_code=400, detail="Numbers must be between 1 and 45")
    
    try:
        result = await analyzer.async_check_winning(numbers, round_no)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_stats():
    """통계 조회"""
    if not analyzer:
        raise HTTPException(status_code=400, detail="Lotto 645 not enabled")
    
    try:
        frequency = await analyzer.async_analyze_number_frequency(50)
        hot_cold = await analyzer.async_get_hot_cold_numbers(20)
        purchase_stats = await analyzer.async_get_purchase_statistics(365)
        
        return {
            "frequency": [
                {"number": f.number, "count": f.count, "percentage": f.percentage} 
                for f in frequency[:10]
            ],
            "hot_numbers": hot_cold.hot_numbers,
            "cold_numbers": hot_cold.cold_numbers,
            "most_frequent": [
                {"number": f.number, "count": f.count, "percentage": f.percentage}
                for f in hot_cold.most_frequent
            ],
            "purchase_stats": {
                "total_purchase_count": purchase_stats.total_purchase_count,
                "total_purchase_amount": purchase_stats.total_purchase_amount,
                "total_winning_count": purchase_stats.total_winning_count,
                "total_winning_amount": purchase_stats.total_winning_amount,
                "win_rate": purchase_stats.win_rate,
                "roi": purchase_stats.roi,
                "rank_distribution": purchase_stats.rank_distribution,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/balance")
async def get_balance():
    """예치금 조회"""
    if not client:
        raise HTTPException(status_code=400, detail="Client not initialized")
    
    try:
        balance = await client.async_get_balance()
        return {
            "deposit": balance.deposit,
            "purchase_available": balance.purchase_available,
            "reservation_purchase": balance.reservation_purchase,
            "withdrawal_request": balance.withdrawal_request,
            "purchase_impossible": balance.purchase_impossible,
            "this_month_accumulated_purchase": balance.this_month_accumulated_purchase,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=60099, log_level="info")
