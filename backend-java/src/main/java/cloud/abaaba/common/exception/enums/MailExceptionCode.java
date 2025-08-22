package cloud.abaaba.common.exception.enums;

import cloud.abaaba.common.exception.ExceptionCode;
import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * MailExceptionCode
 *
 * @author Pig-Gua
 * @date 2025-05-29
 */
@Getter
@AllArgsConstructor
public enum MailExceptionCode implements ExceptionCode {

    PARAM_NOT_NULL("", "邮件%s不能为空"),
    SEND_ERROR("", "邮件发送失败");

    /**
     * 错误码
     */
    private final String code;

    /**
     * 错误信息
     */
    private final String msg;

}
