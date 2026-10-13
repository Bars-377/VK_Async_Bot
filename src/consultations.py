from typing import Dict, Any
import asyncio
from pathlib import Path
import json
from loguru import logger
from aiohttp import ClientSession
import aiohttp
import os

# Класс Store для хранения консультаций
class Store:
    def __init__(self):
        self.consultations: Dict[str, Any] = {}
        self._lock = asyncio.Lock()
        self.cache_file = Path("cache/consultations")
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)

    def _truncate(self, name: str, data: Any) -> Any:
        """Обработка данных консультации"""
        # Если data - это строка, оборачиваем в словарь с ключом message
        if isinstance(data, str):
            return {"message": data}
        # Если data уже словарь, возвращаем как есть
        return data

    def load_from_cache_sync(self):
        """Синхронная загрузка консультаций из кэша"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.consultations = json.load(f)
                logger.info(f"Loaded consultations from cache: {len(self.consultations)} items")
                return True
            except Exception as e:
                logger.error(f"Error loading cache: {e}")
                return False
        return False

    async def load_from_cache(self):
        """Асинхронная загрузка консультаций из кэша"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.consultations = json.load(f)
                logger.info(f"Loaded consultations from cache: {len(self.consultations)} items")
                return True
            except Exception as e:
                logger.error(f"Error loading cache: {e}")
                return False
        return False

    async def subscribe_to_consultations(self, session: ClientSession, *, endpoint: str):
        """Подписка на получение консультаций"""
        cache_file = self.cache_file
        try:
            base_url = os.environ.get('INTERNAL_API_URL', 'http://172.18.11.104:8001')
            url = f"{base_url}/api/v1/shared/subscribe"

            # СТАЛО
            bind_host = os.environ.get("SELF_HOST", "0.0.0.0")
            port = int(os.environ.get("SELF_PORT", "8000"))

            # PUBLIC_HOST — реальный IP/домен, по которому внешний API сможет
            # достучаться до нашего сервера. НЕЛЬЗЯ 0.0.0.0, обычно нельзя и localhost,
            # если API находится не в той же сети/контейнере.
            public_host = os.environ.get("PUBLIC_HOST")
            if not public_host:
                logger.error(
                    "PUBLIC_HOST не задан — вебхук будет зарегистрирован на "
                    f"недостижимый адрес ({bind_host}). Уведомления работать не будут."
                )
                public_host = bind_host  # fallback, скорее всего всё ещё сломано

            webhook_url = f"http://{public_host}:{port}{endpoint}"

            logger.info(f"Subscribing to: {url} with webhook: {webhook_url}")

            async with session.post(
                url,
                json={
                    "webhook_url": webhook_url,
                    "platform": "vk",
                    "resources": []
                },
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status in [200, 201]:
                    consultations_data = await response.json()
                    logger.info(f"Received {len(consultations_data)} consultations from API")

                    # Исправленный парсинг: используем resource вместо name
                    consultations = {}
                    for item in consultations_data:
                        # Проверяем, что в ответе есть нужные поля
                        if "resource" in item and "data" in item:
                            consultations[item["resource"]] = self._truncate(item["resource"], item["data"])
                        else:
                            logger.warning(f"Skipping item without 'resource' or 'data': {item}")

                    # Сохраняем в кэш
                    with open(cache_file, 'w', encoding='utf-8') as f:
                        json.dump(consultations, f, ensure_ascii=False, indent=2)

                    self.consultations = consultations
                    logger.info(f"Subscribed to consultations: {len(consultations)} items")
                    logger.info(f"Available consultations: {list(consultations.keys())}")
                    return consultations
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to subscribe: {response.status} - {error_text}")
                    if await self.load_from_cache():
                        return self.consultations
                    return None

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error(f"Failed to fetch consultations: %s", e)
            if await self.load_from_cache():
                logger.warning("Reading consultations from cache")
                return self.consultations
            else:
                logger.critical("Failed to read consultations from cache")
                return None
