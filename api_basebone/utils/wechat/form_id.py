import logging
import arrow
import redis
from uuid import uuid4
from django_redis import get_redis_connection

logger = logging.getLogger("models")


__all__ = ["FormID"]


class FormID(object):
    """小程序推送使用 form_id
    存储方式 (Redis):
    wxapp:formid:<uid> -> [expire form_id]
    """
    r = None
    prefix = "wxapp:formid"

    USER_FORM_ID_KEY = '{}:{}'

    def __init__(self, form_id, expire):
        self._form_id = form_id
        self.expire = expire
    
    @classmethod
    def redis(cls):
        if not cls.r:
            cls.r = get_redis_connection()
        return cls.r

    @property
    def form_id(self):
        if self._form_id and isinstance(self._form_id, bytes):
            return self._form_id.decode()

    @classmethod
    def get_cache_key(cls, uid):
        return cls.USER_FORM_ID_KEY.format(cls.prefix, uid)

    @classmethod
    def uid_form_id_key(cls, uid):
        '''提供一个 key 生成接口
        '''
        return cls.get_cache_key(uid)

    @classmethod
    def add(cls, uid, form_id, expire=None, force=False):
        ''' 默认 form-id 的超时时间是一周，通过 force 提供插入过期数据，方便测试
            返回None
        '''
        logger.debug("Add %s form-id:%s into redis", uid, form_id)
        if expire is None:
            # 留两个小时作缓冲时间，否则可能会在临界点失效
            expire = arrow.utcnow().timestamp + 604800 - 3600 * 2
        if force or (not cls.__is_expired(expire)):
            cls.redis().zadd(cls.uid_form_id_key(uid), {form_id: expire})

    @classmethod
    def lpop(cls, uid, mock=False):
        ''' pop出第一个可用的form-id,保证数据有效
            return form_id 如果没有可用form-id，返回 None 
        '''
        if mock:
            return cls(uid, uuid4())

        while True:
            result = cls.__lpop(uid)
            # 没有可用的form_id
            if result == []:
                return
            # 拿到一个可用的form_id
            item = result[0]
            obj = cls(item[0], item[1])
            if not cls.__is_expired(obj.expire):
                return obj

    @classmethod
    def __lpop(cls, uid):
        with cls.redis().pipeline(transaction=True) as pipe:
            key = cls.uid_form_id_key(uid)
            pipe.zremrangebyscore(key, "-inf", arrow.now().timestamp + 2)
            pipe.zrange(key, 0, 0, withscores=True)
            pipe.zremrangebyrank(key, 0, 0)
            return pipe.execute()[1]

    @classmethod
    def batch_lpop(cls, uuids, mock=False):
        ''' 批量获取用户的form-id接口，如果用户有可用form-id返回最近可用的，否则不返回
            如果用户没有可用的form-id，这个接口不应该再重试
            return 一个dict uuid <-> form-id
        '''
        result = {}
        if uuids == []:
            return result

        if mock:
            for uuid in uuids:
                result[uuid] = cls(uuid, uuid4())
            return result

        with cls.redis().pipeline(transaction=True) as pipe:
            pipe.multi()
            for uuid in uuids:
                key = cls.uid_form_id_key(uuid)
                pipe.zremrangebyscore(key, "-inf", arrow.now().timestamp)
                pipe.zrange(key, 0, 0, withscores=True)
                pipe.zremrangebyrank(key, 0, 0)
            items = pipe.execute()

            data = [items[i] for i in range(1, len(items), 3)]
            for uuid, res in zip(uuids, data):
                if res != []:
                    item = res[0]
                    if cls.__is_expired(item[1]):
                        # 正常系统，超时的uuid应该不多
                        logger.info("expire form id: uid <%s> formID <%s>", uuid, item[0])
                        result[uuid] = cls.lpop(uuid)
                    else:
                        result[uuid] = cls(item[0], item[1])
                else:
                    logger.info("user <%s> no form id can use", uuid)
        logger.info("batch_lpop: <%d> want got <%d>", len(uuids), len(result))
        return result

    @classmethod
    def __delete(cls, key):
        """ 删除这个操作要保持 atom
        """
        logger.info("delete key: %s", key)
        with cls.redis().pipeline(transaction=True) as pipe:
            try:
                pipe.zremrangebyscore(key, "-inf", arrow.now().timestamp)
                pipe.watch(key)
                if pipe.zcard(key) <= 0:
                    pipe.delete(key)
                pipe.execute()
            except redis.WatchError:
                logger.info("update during transaction")
            finally:
                pipe.unwatch()

    @classmethod
    def __clear(cls, key):
        if cls.__user_expired(key):
            cls.__delete(key)
        else:
            cls.redis().zremrangebyscore(key, "-inf", arrow.now().timestamp)

    @classmethod
    def __user_expired(cls, key):
        result = cls.redis().zrange(key, -1, -1, withscores=True)
        if result == []:
            return True
        return cls.__is_expired(result[0][1])

    @classmethod
    def __is_expired(cls, expire):
        if int(expire) < arrow.now().timestamp:
            return True
        return False

    @classmethod
    def batch_clear(cls):
        ''' 清理数据接口，为了保证写入的正确性，效率非常底，应该在用户不活跃，夜深人静的时候调用
        '''
        for key in cls.redis().scan_iter(cls.get_cache_key("*"), count=100):
            logger.info("clear key: %s", key)
            cls.__clear(key)
