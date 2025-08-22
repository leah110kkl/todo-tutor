package cloud.abaaba.common.exception.handler;

import cloud.abaaba.common.exception.BusinessException;
import cloud.abaaba.common.exception.Response;
import cloud.abaaba.common.exception.enums.GlobalExceptionCode;
import jakarta.servlet.http.HttpServletRequest;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

/**
 * GlobalExceptionHandler 全局异常处理
 *
 * @author Pig-Gua
 * @date 2025-05-24
 */
@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {

    /**
     * 用于处理全局异常拦截无法捕获到的位置
     *
     * @param ex      异常
     * @param request 请求信息
     * @return 通用返回
     */
    public Response<?> handle(Throwable ex, HttpServletRequest request) {
        if (ex instanceof BusinessException) {
            return businessExceptionHandler((BusinessException) ex, request);
        } else {
            return unknownExceptionHandler(ex, request);
        }
    }

    /**
     * 业务异常
     */
    @ExceptionHandler(BusinessException.class)
    public Response<?> businessExceptionHandler(BusinessException ex, HttpServletRequest request) {
        log.info("[businessExceptionHandler]: {}-{}", ex.getExceptionCode().getCode(), ex.getExceptionCode().getMsg());
        return Response.error(ex.getExceptionCode());
    }

    /**
     * 兜底处理
     */
    @ExceptionHandler(Throwable.class)
    public Response<?> unknownExceptionHandler(Throwable ex, HttpServletRequest request) {
        log.error("[unknownExceptionHandler]", ex);
        return Response.error(GlobalExceptionCode.UNKNOWN_ERROR);
    }

}
