package cloud.abaaba.common.security;

import cloud.abaaba.common.exception.BusinessException;
import cloud.abaaba.common.exception.enums.LoginExceptionCode;
import cloud.abaaba.common.redis.RedisClient;
import cloud.abaaba.common.trace.ReqInfo;
import cloud.abaaba.common.trace.ReqInfoContextHolder;
import cloud.abaaba.service.domain.UserDO;
import cloud.abaaba.service.impl.AuthServiceImpl;
import cn.hutool.core.util.ReUtil;
import jakarta.annotation.Resource;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

/**
 * SecurityFilter
 *
 * @author Pig-Gua
 * @date 2025-06-14
 */
@Order(99)
@Component
public class SecurityFilter extends OncePerRequestFilter {

    @Resource
    private RedisClient redisClient;

    /**
     * 白名单接口
     */
    public static final String[] IGNORE_URLS = new String[]{
            "/auth/loginByUsername",
            "/auth/sendLoginEmail",
            "/auth/loginByEmail",

            "/doc.html",
            "/favicon.ico",
            "/v3/api-docs(/.*)?",
            ".*\\.js$",    // 匹配所有.js文件
            ".*\\.css$",   // 匹配所有.css文件
    };

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain) throws IOException, ServletException {
        ReqInfo reqInfo = ReqInfoContextHolder.getReqInfo();

        // 获取token
        String token = request.getHeader("token");
        reqInfo.setToken(token);

        // 登录认证
        String requestURI = request.getRequestURI();
        if (!isIgnoreUrl(requestURI)) {
            UserDO userDO = (UserDO) redisClient.get(AuthServiceImpl.LOGIN_TOKEN + reqInfo.getToken());
            if (userDO == null) {
                throw new BusinessException(LoginExceptionCode.TOKEN_NOT_FOUND);
            }
            reqInfo.setCurrentUser(userDO);
        }

        // 放行
        filterChain.doFilter(request, response);
    }

    /**
     * 判断是否为白名单URL
     * @param requestURI 请求URI
     * @return 是否为白名单
     */
    private boolean isIgnoreUrl(String requestURI) {
        for (String pattern : IGNORE_URLS) {
            if (ReUtil.isMatch(pattern, requestURI)) {
                return true;
            }
        }
        return false;
    }

}
