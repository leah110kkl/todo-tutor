package cloud.abaaba.common.exception;

import lombok.Getter;

/**
 * ErrorCode 业务异常
 *
 * @author Pig-Gua
 * @date 2025-05-24
 */
@Getter
public class BusinessException extends RuntimeException {

    private final ExceptionCode exceptionCode;

    public BusinessException(ExceptionCode exceptionCode, Object... args) {
        this.exceptionCode = new ExceptionCode() {
            @Override
            public String getCode() {
                return exceptionCode.getCode();
            }

            @Override
            public String getMsg() {
                return String.format(exceptionCode.getMsg(), args);
            }
        };
    }

}
