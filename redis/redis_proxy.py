# !/usr/bin/python
# coding=utf-8

import redis
import time
import threading
import random


r = redis.Redis(host='192.168.208.129', port=6379, db=0)


# 字符串类型
def demo_string():
    r.set('name', 'jack')
    r.set('email', 'jackjack@yahoo.com')
    print r.get('name')
    print r.get('email')
    r.incr('age')
    r.incr('age', 20)
    print r.get('age')
    r.decr('age', 5)
    print r.get('age')
    print r.strlen('name')

    r.mset({'key1': 'v1', 'key2': 'v2'})
    print r.mget(['key1', 'key2'])


# 散列表
def demo_hash_table():
    num = 12
    key = "post:%d" % num
    r.hset(key, 'title', 'hello world')
    r.hset(key, 'author', 'jack')
    r.hset(key, 'time', '2016-12-16')
    r.hset(key, 'content', 'test')
    print r.hgetall(key)


# transaction事务
def demo_transaction():
    r.set('file', 'test.cc')
    with r.pipeline() as pipe:
        while True:
            try:
                # 先关注一个key
                pipe.watch('file')
                pipe.multi()
                pipe.set('file', 'test1.cc')
                pipe.execute()
                break
            except WatchError:
                continue
    print r.get('file')


# 生存时间 限时优惠 缓存 验证码等 多了一点时间就会删除这些数据 redis中可以使用expire实现
# persist set get命令都可以消除键的生存时间
# expireat 和 expire 区别在于前者使用unix时间作为键的生存时间的截止时间
def demo_expire():
    r.set('code', '123456')
    ret = r.expire('code', 6)
    if ret:
        print 'expire set success'
    else:
        return False
    while True:
        if r.exists('code'):
            print r.get('code')
            print r.ttl('code')
        else:
            print 'code timeout del it'
            break
        time.sleep(1)


# 减轻服务器压力，限制单用户一段时间访问量
# 没访问一次增加1 并设置生存时间1分钟即可
def visit(ip):
    key = 'rate.limiting:%s' % ip
    if r.exists(key):
        times = r.incr(key)
        print times
        if times > 50:
            print 'visit too frequent'
            return False
    else:
        with r.pipeline() as pipe:
            pipe.multi()
            r.incr(key)
            r.expire(key, 30)
            pipe.execute()
    return True


# 限制单用户时间段内访问量算法优化
def optimize_visit(ip):
    lt = 'lrate.limiting:%s' % ip
    length = r.llen(lt)
    if length < 10:
        r.lpush(lt, time.time())
        print r.l
    else:
        te = float(r.lindex(lt, 1))
        if time.time() - te < 60:
            print "visit too frequent optimize visit"
            return False
        else:
            r.lpush(lt, time.time())
            r.ltrim(lt, 0, 9)
    return True


def demo_pressure():
    ip = '192.168.208.129'
    # key = 'rate.limiting:%s' % ip
    while True:
        if not visit(ip):
            print 'you can not visit'
            break
    while True:
        if optimize_visit(ip):
            print 'you can not visit optimize visit'
            break


# 排序sort sort可以对列表类型，集合类型和有序集合类型进行排序
def demo_sort():
    set_name = 'letters'
    set_name1 = 'letters1'
    r.sadd(set_name, 'a', 'k', 'h', 'b', 'd')
    r.sadd(set_name1, 'y', 'k', 'u', 'c', 'd')
    print r.sdiff(set_name, set_name1)
    print r.sdiff(set_name1, set_name)
    set_name2 = 'integer'
    r.sadd(set_name2, 100, 2, 3, 9, 10, 89)
    print r.sort(set_name2)
    print r.sort(set_name2, None, None, None, None, True)
    # 使用by sort 将lt中元素排序，按照item:*的值进行
    lt = 'sore'
    r.lpush(lt, 1, 2, 3)
    r.set('item:1', 50)
    r.set('item:2', -10)
    r.set('item:3', 100)
    print r.sort(lt, None, None, 'item:*')


def insert_data(queue, queue1):
    count = 0
    while True:
        if count >= 10:
            break
        else:
            r.lpush(queue1, random.random())
            r.lpush(queue, random.randint(1, 999))
            count += 1
            time.sleep(1)
    pass


def demo_queue(inst, queue, queue1):
    """
    redis 实现普通的任务队列
    brpop 可以同时检测多个队列，利用这个机制可以实现优先队列，多个键则是从左到右的顺序取出
    """
    while True:
        task = inst.brpop((queue, queue1), 0)
        print task
    pass


if __name__ == '__main__':
    demo_string()
    demo_hash_table()
    demo_transaction()
    # demo_expire()
    # demo_pressure()
    demo_sort()
    queue_name = 'queue'
    queue_name1 = 'queue1'
    thread = threading.Thread(target=demo_queue, args=(r, queue_name, queue_name1))
    thread.start()
    insert_data(queue_name, queue_name1)

