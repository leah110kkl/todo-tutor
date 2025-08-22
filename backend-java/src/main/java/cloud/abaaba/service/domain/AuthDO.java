package cloud.abaaba.service.domain;

import lombok.Data;

/**
 * AuthDO
 *
 * @author Pig-Gua
 * @date 2025-06-14
 */
@Data
public class AuthDO {

    /**
     * 用户ID
     */
    private Long userId;

    /**
     * 用户名
     */
    private String username;

    /**
     * 邮箱
     */
    private String email;

    /**
     * 密码
     */
    private String password;

    /**
     * 验证码
     */
    private String code;

    // =================================================================

    /**
     * 登录Token
     */
    private String token;

    /**
     * 用户信息
     */
    private UserDO userDO;

}
