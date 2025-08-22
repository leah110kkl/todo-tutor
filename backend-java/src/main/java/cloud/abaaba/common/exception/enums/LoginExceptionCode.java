package cloud.abaaba.common.exception.enums;

import cloud.abaaba.common.exception.ExceptionCode;
import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * LoginExceptionCode
 *
 * @author Pig-Gua
 * @date 2025-05-31
 */
@Getter
@AllArgsConstructor
public enum LoginExceptionCode implements ExceptionCode {

    EMAIL_EXIST("010101", "该账号已存在"),
    EMAIL_NOT_EXIST("", "该账号未注册"),
    TOKEN_NOT_FOUND("010103", "登录状态已过期，请重新登录"), // 前端有此code的特殊判断
    REGISTER_CAPTCHA_ERROR("", "账号注册验证码错误"),
    RESET_CAPTCHA_ERROR("", "账号重置验证码错误"),
    USERNAME_NOT_FOUND("", "该用户名没有注册"),
    EMAIL_NOT_FOUND("", "该邮箱没有注册"),
    CODE_NOT_MATCH("", "验证码错误"),
    PASSWORD_ERROR("", "账号或密码错误");

    /**
     * 错误码
     */
    private final String code;

    /**
     * 错误信息
     */
    private final String msg;

}
