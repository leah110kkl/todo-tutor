package cloud.abaaba.common.exception.enums;


import cloud.abaaba.common.exception.ExceptionCode;
import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * GlobalException 全局异常码枚举
 *
 * @author Pig-Gua
 * @date 2025-05-24
 */
@Getter
@AllArgsConstructor
public enum GlobalExceptionCode implements ExceptionCode {

    SUCCESS("200", "请求成功"),
    UNKNOWN_ERROR("500", "系统异常"),
    // %s 方便临时调用，按照规范不应该使用
    UNKNOWN_OTHER("999", "%s");

    /**
     * 错误码
     */
    private final String code;

    /**
     * 错误信息
     */
    private final String msg;

}
