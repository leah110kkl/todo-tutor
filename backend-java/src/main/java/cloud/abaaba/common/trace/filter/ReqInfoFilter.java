package cloud.abaaba.common.trace.filter;

import cn.hutool.core.lang.UUID;
import cn.hutool.core.util.StrUtil;
import cloud.abaaba.common.exception.Response;
import cloud.abaaba.common.exception.handler.GlobalExceptionHandler;
import cloud.abaaba.common.trace.ReqInfo;
import cloud.abaaba.common.trace.ReqInfoContextHolder;
import cloud.abaaba.common.utils.ServletUtil;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.slf4j.MDC;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import jakarta.annotation.Resource;
import java.io.IOException;

/**
 * ReqInfoFilter 记录请求信息，顺序需要放在所有filter之前
 *
 * @author Pig-Gua
 * @date 2025-05-24
 */
@Order(Integer.MIN_VALUE)
@Component
public class ReqInfoFilter extends OncePerRequestFilter {

    @Resource
    private GlobalExceptionHandler globalExceptionHandler;

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain) throws ServletException, IOException {
        try {
            // 创建新的请求上下文信息
            ReqInfo reqInfo = ReqInfoContextHolder.createEmptyContext();

            // 优先从请求头获取traceId，没有再随机生成
            String traceId = request.getHeader("traceId");
            traceId = StrUtil.isBlank(traceId) ? UUID.fastUUID().toString() : traceId;
            reqInfo.setTraceId(traceId);

            // 日志记录traceId
            MDC.put("traceId", traceId);

            // 放行
            filterChain.doFilter(request, response);

        } catch (Throwable ex) {
            // 处理异常，写入响应
            Response<?> errorResponse = globalExceptionHandler.handle(ex, request);
            ServletUtil.writeJson(response, errorResponse);
        } finally {
            // 清理请求上下文信息，日志上下文信息
            ReqInfoContextHolder.clear();
            MDC.clear();
        }
    }

}
