package cloud.abaaba.service;

import cloud.abaaba.service.domain.AuthDO;

/**
 * AuthService
 *
 * @author Pig-Gua
 * @date 2025-05-27
 */
public interface AuthService {

    /**
     * 发送注册验证码
     *
     * @param authDO authDO
     */
    void sendRegisterEmail(AuthDO authDO);

    /**
     * 注册
     *
     * @param authDO authDO
     */
    void register(AuthDO authDO);

    /**
     * 登录（用户名+密码）
     *
     * @param authDO authDO
     * @return 用户详情
     */
    AuthDO loginByUsername(AuthDO authDO);

    /**
     * 登录场景-发送邮箱验证码
     *
     * @param authDO authDO
     */
    void sendLoginEmail(AuthDO authDO);

    /**
     * 登录（邮箱+验证码）
     */
    AuthDO loginByEmail(AuthDO authDO);

    /**
     * 登出
     */
    void logout();

    /**
     * 发送重置密码邮箱验证码
     *
     * @param authDO authDO
     */
    void sendResetPasswordEmail(AuthDO authDO);

    /**
     * 重置密码
     *
     * @param authDO authDO
     */
    void resetPassword(AuthDO authDO);

    /**
     * 发送重置邮箱验证码
     *
     * @param authDO authDO
     */
    void sendResetEmailEmail(AuthDO authDO);

    /**
     * 重置邮箱
     *
     * @param authDO authDO
     */
    void resetEmail(AuthDO authDO);

}
