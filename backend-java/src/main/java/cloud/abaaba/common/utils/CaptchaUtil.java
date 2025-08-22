package cloud.abaaba.common.utils;

import java.util.Random;

/**
 * CaptchaUtil
 *
 * @author Pig-Gua
 * @date 2025-05-30
 */
public class CaptchaUtil {

    /**
     * 生成6位纯数字验证码
     *
     * @return 6位验证码字符串
     */
    public static String generateNumericCode() {
        int min = 100000; // 最小6位数
        int max = 999999; // 最大6位数
        return String.valueOf(new Random().nextInt(max - min + 1) + min);
    }

    /**
     * 生成指定位数的纯数字验证码
     *
     * @param length 验证码长度
     * @return 验证码字符串
     */
    public static String generateNumericCode(int length) {
        StringBuilder code = new StringBuilder();
        Random random = new Random();
        for (int i = 0; i < length; i++) {
            code.append(random.nextInt(10)); // 0~9之间的随机数
        }
        return code.toString();
    }

}
