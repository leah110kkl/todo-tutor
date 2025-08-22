package cloud.abaaba.common.utils;

import cn.hutool.crypto.digest.MD5;

/**
 * EncryptUtil
 *
 * @author Pig-Gua
 * @date 2025-06-14
 */
public class EncryptUtil {

    /**
     * md5编码
     *
     * @param str 原始字符串
     * @return 编码后字符串
     */
    public static String md5(String str) {
        return MD5.create().digestHex(str);
    }

    /**
     * md5编码-比较
     *
     * @param rawStr    原始字符串
     * @param encodeStr 编码后字符串
     * @return 是否相等
     */
    public static boolean md5Equals(String rawStr, String encodeStr) {
        return md5(rawStr).equals(encodeStr);
    }

}
