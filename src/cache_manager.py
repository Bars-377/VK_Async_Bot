import hashlib
from loguru import logger
from datetime import date

# Класс для управления кешем
class CacheManager:
    def __init__(self):
        self.cache = {}
        self.cache_date = None

    def _get_today(self):
        return date.today()

    def _get_cache_key(self, *args, **kwargs):
        """Создает уникальный ключ для кеша"""
        key_data = f"{args}{kwargs}".encode('utf-8')
        return hashlib.md5(key_data).hexdigest()

    def get(self, key):
        """Получает данные из кеша, если они актуальны"""
        today = self._get_today()

        # Если дата изменилась - очищаем кеш
        if self.cache_date != today:
            self.clear()
            self.cache_date = today
            return None

        return self.cache.get(key)

    def set(self, key, value):
        """Сохраняет данные в кеш"""
        today = self._get_today()

        if self.cache_date != today:
            self.clear()
            self.cache_date = today

        self.cache[key] = value

    def clear(self):
        """Очищает кеш"""
        self.cache.clear()
        logger.info("Cache cleared")

    def get_or_set(self, key, getter_func, *args, **kwargs):
        """
        Получает данные из кеша или вызывает функцию для их получения
        """
        cached_data = self.get(key)
        if cached_data is not None:
            logger.info(f"Cache hit for key: {key}")
            return cached_data

        logger.info(f"Cache miss for key: {key}, fetching data...")
        data = getter_func(*args, **kwargs)
        self.set(key, data)
        return data

    async def get_or_set_async(self, key, async_getter_func, *args, **kwargs):
        """
        Асинхронно получает данные из кеша или вызывает функцию для их получения
        """
        cached_data = self.get(key)
        if cached_data is not None:
            logger.info(f"Cache hit for key: {key}")
            return cached_data

        logger.info(f"Cache miss for key: {key}, fetching data asynchronously...")
        data = await async_getter_func(*args, **kwargs)
        self.set(key, data)
        return data
