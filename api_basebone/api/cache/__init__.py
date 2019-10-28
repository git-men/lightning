from django.core.cache import cache
from ...utils.redis import redis_client
from django.conf import settings


class ApiCache:

    # 小程序用户 session_key, 键值参数使用 appid 和 用户的 id
    API_KEY = "api:slug:{}"

    def set_api_config(self, slug, api_config, pipe=None):
        """缓存api配置"""
        pipe = pipe if pipe else redis_client
        key = cache.make_key(self.API_KEY.format(slug))
        pipe.set(key, api_config)
        cache_time = getattr(settings, 'API_CACHE_TIME', 1 * 60)
        pipe.expire(key, cache_time)

    def get_api_config(self, slug, pipe=None):
        """读api缓存"""
        pipe = pipe if pipe else redis_client
        key = cache.make_key(self.API_KEY.format(slug))
        return pipe.get(key)

    def delete_api_config(self, slug, pipe=None):
        pipe = pipe if pipe else redis_client
        key = cache.make_key(self.API_KEY.format(slug))
        pipe.delete(key)


api_cache = ApiCache()
