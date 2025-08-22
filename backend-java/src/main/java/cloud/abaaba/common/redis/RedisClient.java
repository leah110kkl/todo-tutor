package cloud.abaaba.common.redis;

import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.data.redis.core.script.DefaultRedisScript;
import org.springframework.stereotype.Component;

import java.util.*;
import java.util.concurrent.TimeUnit;

/**
 * RedisClient - 基于 RedisTemplate 的封装工具类
 *
 * @author Pig-Gua
 * @date 2025-05-30
 */
@Component
public class RedisClient {

    private final RedisTemplate<String, Object> redisTemplate;

    private static final int BIT_SIZE = 1 << 25; // 32MB内存，约可容纳千万级数据
    private static final int[] SEEDS = new int[]{3, 5, 7, 11, 13, 31, 37, 61};

    private final HashFunction[] hashFunctions = new HashFunction[SEEDS.length];

    public RedisClient(RedisTemplate<String, Object> redisTemplate) {
        this.redisTemplate = redisTemplate;
        for (int i = 0; i < SEEDS.length; i++) {
            hashFunctions[i] = new HashFunction(SEEDS[i]);
        }
    }

    // ===================== 通用操作 =====================

    /**
     * 设置键值对，并指定过期时间
     */
    public void set(String key, Object value, long timeout, TimeUnit unit) {
        redisTemplate.opsForValue().set(key, value, timeout, unit);
    }

    /**
     * 设置键值对，默认永不过期
     */
    public void set(String key, Object value) {
        redisTemplate.opsForValue().set(key, value);
    }

    /**
     * 获取缓存值
     */
    public Object get(String key) {
        return redisTemplate.opsForValue().get(key);
    }

    /**
     * 删除一个或多个键
     */
    public void delete(String... keys) {
        redisTemplate.delete(Arrays.asList(keys));
    }

    /**
     * 判断键是否存在
     */
    public boolean exists(String key) {
        return redisTemplate.hasKey(key);
    }

    /**
     * 设置键的过期时间
     */
    public boolean expire(String key, long timeout, TimeUnit unit) {
        return redisTemplate.expire(key, timeout, unit);
    }

    /**
     * 获取键的剩余生存时间（秒）
     */
    public Long getExpire(String key) {
        return redisTemplate.getExpire(key);
    }

    // ===================== Hash 操作 =====================

    /**
     * 向 Hash 表中放入字段值
     */
    public void hSet(String key, String hashKey, Object value) {
        redisTemplate.opsForHash().put(key, hashKey, value);
    }

    /**
     * 获取 Hash 表中的字段值
     */
    public Object hGet(String key, String hashKey) {
        return redisTemplate.opsForHash().get(key, hashKey);
    }

    /**
     * 获取整个 Hash 表
     */
    public Map<Object, Object> hGetAll(String key) {
        return redisTemplate.opsForHash().entries(key);
    }

    /**
     * 删除 Hash 表中的字段
     */
    public void hDel(String key, Object... hashKeys) {
        redisTemplate.opsForHash().delete(key, hashKeys);
    }

    // ===================== List 操作 =====================

    /**
     * 在列表左侧插入元素
     */
    public Long lPush(String key, Object... values) {
        return redisTemplate.opsForList().leftPushAll(key, values);
    }

    /**
     * 在列表右侧插入元素
     */
    public Long rPush(String key, Object... values) {
        return redisTemplate.opsForList().rightPushAll(key, values);
    }

    /**
     * 移除并返回列表最左边的元素
     */
    public Object lPop(String key) {
        return redisTemplate.opsForList().leftPop(key);
    }

    /**
     * 移除并返回列表最右边的元素
     */
    public Object rPop(String key) {
        return redisTemplate.opsForList().rightPop(key);
    }

    /**
     * 获取列表指定范围内的元素
     */
    public List<Object> lRange(String key, long start, long end) {
        return redisTemplate.opsForList().range(key, start, end);
    }

    // ===================== Set 操作 =====================

    /**
     * 向集合中添加元素
     */
    public Long sAdd(String key, Object... values) {
        return redisTemplate.opsForSet().add(key, values);
    }

    /**
     * 获取集合中的所有成员
     */
    public Set<Object> sMembers(String key) {
        return redisTemplate.opsForSet().members(key);
    }

    /**
     * 从集合中移除一个或多个成员
     */
    public Long sRem(String key, Object... values) {
        return redisTemplate.opsForSet().remove(key, values);
    }

    // ===================== ZSet（有序集合）=====================

    /**
     * 添加一个成员到有序集合
     */
    public Boolean zAdd(String key, Object value, double score) {
        return redisTemplate.opsForZSet().add(key, value, score);
    }

    /**
     * 获取有序集合中指定范围的成员（带分数）
     */
    public Set<Object> zRange(String key, long start, long end) {
        return redisTemplate.opsForZSet().range(key, start, end);
    }

    /**
     * 从有序集合中删除一个或多个成员
     */
    public Long zRem(String key, Object... values) {
        return redisTemplate.opsForZSet().remove(key, values);
    }

    // ===================== 分布式锁 =====================

    /**
     * 获取分布式锁（SET_NX 方式）
     *
     * @param lockKey 锁的 key
     * @param requestId 请求标识（唯一ID，如UUID）
     * @param expireTime 过期时间（秒）
     * @return 是否获取成功
     */
    public boolean tryLock(String lockKey, String requestId, long expireTime) {
        return Boolean.TRUE.equals(redisTemplate.opsForValue().setIfAbsent(lockKey, requestId, expireTime, TimeUnit.SECONDS));
    }

    /**
     * 释放分布式锁（Lua脚本保证原子性）
     */
    public void releaseLock(String lockKey, String requestId) {
        String script = "if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('del', KEYS[1]) else return 0 end";

        // 使用 DefaultRedisScript 包装脚本
        DefaultRedisScript<Long> redisScript = new DefaultRedisScript<>();
        redisScript.setScriptText(script);
        redisScript.setResultType(Long.class);

        // 执行脚本
        redisTemplate.execute(redisScript, Collections.singletonList(lockKey), requestId);
    }

    // ===================== 布隆过滤器（用于防缓存穿透） =====================

    /**
     * 添加值到布隆过滤器
     */
    public void bloomAdd(String key, String value) {
        for (HashFunction f : hashFunctions) {
            long hash = f.hash(value);
            long bitIndex = Math.abs(hash % BIT_SIZE);
            redisTemplate.opsForValue().setBit(key, bitIndex, true);
        }
    }

    /**
     * 判断是否存在于布隆过滤器中
     */
    public boolean bloomContains(String key, String value) {
        for (HashFunction f : hashFunctions) {
            long hash = f.hash(value);
            long bitIndex = Math.abs(hash % BIT_SIZE);
            if (Boolean.FALSE.equals(redisTemplate.opsForValue().getBit(key, bitIndex))) {
                return false;
            }
        }
        return true;
    }

    // 内部哈希函数类
    private static class HashFunction {
        private final int seed;

        public HashFunction(int seed) {
            this.seed = seed;
        }

        public long hash(String value) {
            long result = 0;
            for (int i = 0; i < value.length(); i++) {
                result = result * seed + value.charAt(i);
            }
            return result;
        }
    }

    // ===================== 限流器实现（令牌桶算法 + Lua 脚本） =====================

    private static final String RATE_LIMIT_SCRIPT =
        "local key = KEYS[1]\n" +
        "local max = tonumber(ARGV[1])\n" +
        "local rate = tonumber(ARGV[2])\n" +
        "local now = tonumber(ARGV[3])\n" +
        "\n" +
        "local current = redis.call(\"GET\", key)\n" +
        "if not current then\n" +
        "    redis.call(\"SETEX\", key, 1, rate - 1)\n" +
        "    return true\n" +
        "end\n" +
        "\n" +
        "if tonumber(current) > 0 then\n" +
        "    redis.call(\"DECR\", key)\n" +
        "    return true\n" +
        "else\n" +
        "    return false\n" +
        "end";

    /**
     * 限流判断（每秒允许 max 次访问，每秒补充 rate 个令牌）
     *
     * @param key 限流 key（如：user:1001）
     * @param max 最大容量
     * @param rate 补充速率
     * @return 是否允许访问
     */
    public boolean isAllowed(String key, int max, int rate) {
        Long now = System.currentTimeMillis() / 1000;
        List<String> keys = Collections.singletonList(key);

        // 创建 RedisScript 对象
        DefaultRedisScript<Boolean> script = new DefaultRedisScript<>();
        script.setScriptText(RATE_LIMIT_SCRIPT);
        script.setResultType(Boolean.class);

        // 执行脚本
        return redisTemplate.execute(script, keys, max, rate, now);
    }

}
