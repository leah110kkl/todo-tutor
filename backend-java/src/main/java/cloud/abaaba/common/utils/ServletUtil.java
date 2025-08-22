package cloud.abaaba.common.utils;

import cn.hutool.extra.servlet.JakartaServletUtil;
import cn.hutool.json.JSONUtil;
import org.springframework.http.MediaType;

import jakarta.servlet.http.HttpServletResponse;

/**
 * ServletUtils
 *
 * @author Pig-Gua
 * @date 2025-05-24
 */
public class ServletUtil {

    /**
     * 返回 JSON 字符串
     *
     * @param response 响应
     * @param object 对象，会序列化成 JSON 字符串
     */
    @SuppressWarnings("deprecation")
    public static void writeJson(HttpServletResponse response, Object object) {
        String content = JSONUtil.toJsonStr(object);
        JakartaServletUtil.write(response, content, MediaType.APPLICATION_JSON_UTF8_VALUE);
    }

}
