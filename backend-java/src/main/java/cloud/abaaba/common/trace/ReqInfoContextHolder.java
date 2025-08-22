package cloud.abaaba.common.trace;

import com.alibaba.ttl.TransmittableThreadLocal;

/**
 * ReqInfoContextHolder 请求信息上下文
 *
 * @author Pig-Gua
 * @date 2025-05-24
 */
public class ReqInfoContextHolder {

    /**
     * 跨线程传递ThreadLocal，详见 TL，ITL，TTL 区别
     */
    private static final ThreadLocal<ReqInfo> CONTEXT = new TransmittableThreadLocal<>();

    /**
     * 创建空的请求上下文信息
     */
    public static ReqInfo createEmptyContext() {
        ReqInfo reqInfo = new ReqInfo();
        CONTEXT.set(reqInfo);
        return reqInfo;
    }

    /**
     * 获取当前线程的请求上下文信息，若不存在则自动创建一个新的
     */
    public static ReqInfo getReqInfo() {
        ReqInfo reqInfo = CONTEXT.get();
        if (reqInfo == null) {
            reqInfo = new ReqInfo();
            CONTEXT.set(reqInfo);
        }
        return reqInfo;
    }

    /**
     * 清除当前线程的请求上下文，防止内存泄漏
     */
    public static void clear() {
        CONTEXT.remove();
    }

}
