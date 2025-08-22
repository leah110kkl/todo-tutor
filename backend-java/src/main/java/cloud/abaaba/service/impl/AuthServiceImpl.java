package cloud.abaaba.service.impl;

import cloud.abaaba.common.exception.BusinessException;
import cloud.abaaba.common.exception.enums.GlobalExceptionCode;
import cloud.abaaba.common.exception.enums.LoginExceptionCode;
import cloud.abaaba.common.mail.MailClient;
import cloud.abaaba.common.mail.template.LoginCodeTemplate;
import cloud.abaaba.common.mail.template.ResetEmailCodeTemplate;
import cloud.abaaba.common.mail.template.ResetPasswordCodeTemplate;
import cloud.abaaba.common.redis.RedisClient;
import cloud.abaaba.common.trace.ReqInfoContextHolder;
import cloud.abaaba.common.utils.CaptchaUtil;
import cloud.abaaba.common.utils.EncryptUtil;
import cloud.abaaba.service.AuthService;
import cloud.abaaba.service.domain.AuthDO;
import cloud.abaaba.service.domain.UserDO;
import cloud.abaaba.service.repo.UserRepo;
import cn.hutool.core.util.IdUtil;
import jakarta.annotation.Resource;
import org.springframework.stereotype.Service;

import java.util.concurrent.TimeUnit;

/**
 * LoginServiceImpl
 *
 * @author Pig-Gua
 * @date 2025-05-28
 */
@Service
public class AuthServiceImpl implements AuthService {

    @Resource
    private UserRepo userRepo;
    @Resource
    private MailClient mailClient;
    @Resource
    private RedisClient redisClient;

    public static final String LOGIN_USER = "todo-tutor:login:user:";
    public static final String LOGIN_TOKEN = "todo-tutor:login:token:";

    public static final String LOGIN_CAPTCHA_KEY = "todo-tutor:captcha:login:";
    public static final String RESET_PASSWORD_CAPTCHA_KEY = "todo-tutor:captcha:reset-password:";
    public static final String RESET_EMAIL_CAPTCHA_KEY = "todo-tutor:captcha:reset-email:";

    @Override
    public AuthDO loginByUsername(AuthDO authDO) {
        // 账号密码校验
        UserDO detail = userRepo.selectByUsername(authDO.getUsername());
        if (detail == null) {
            throw new BusinessException(LoginExceptionCode.USERNAME_NOT_FOUND);
        }
        if (!EncryptUtil.md5Equals(authDO.getPassword(), detail.getPassword())) {
            throw new BusinessException(LoginExceptionCode.PASSWORD_ERROR);
        }

        // 生成token
        String token = IdUtil.fastSimpleUUID();
        redisClient.sAdd(LOGIN_USER + detail.getUserId(), token);
        redisClient.set(LOGIN_TOKEN + token, detail, 1, TimeUnit.DAYS);

        // 返回登录信息
        AuthDO loginInfo = new AuthDO();
        loginInfo.setToken(token);
        loginInfo.setUserDO(detail);
        return loginInfo;
    }

    @Override
    public void sendLoginEmail(AuthDO loginDTO) {
        if (loginDTO.getEmail() == null || userRepo.selectByEmail(loginDTO.getEmail()) == null) {
            throw new BusinessException(GlobalExceptionCode.UNKNOWN_OTHER, "该邮箱未被注册");
        }
        // 生成验证码，过期时间 5分钟
        String code = CaptchaUtil.generateNumericCode();
        int expire = 5;

        // 发送邮件
        redisClient.set(LOGIN_CAPTCHA_KEY + loginDTO.getEmail(), code, expire, TimeUnit.MINUTES);
        mailClient.send(LoginCodeTemplate.getInstance(code, expire), loginDTO.getEmail());
    }

    @Override
    public AuthDO loginByEmail(AuthDO authDO) {
        // 校验验证码
        String sendCode = (String) redisClient.get(LOGIN_CAPTCHA_KEY + authDO.getEmail());
        if (!authDO.getCode().equals(sendCode)) {
            throw new BusinessException(LoginExceptionCode.CODE_NOT_MATCH);
        }
        redisClient.delete(LOGIN_CAPTCHA_KEY + authDO.getEmail());

        // 账号是否存在
        UserDO detail = userRepo.selectByEmail(authDO.getEmail());
        if (detail == null) {
            throw new BusinessException(GlobalExceptionCode.UNKNOWN_OTHER, "未找到该邮箱的用户信息");
        }

        // 生成token
        String token = IdUtil.fastSimpleUUID();
        redisClient.sAdd(LOGIN_USER + detail.getUserId(), token);
        redisClient.set(LOGIN_TOKEN + token, detail, 1, TimeUnit.DAYS);

        // 返回登录信息
        AuthDO loginInfo = new AuthDO();
        loginInfo.setToken(token);
        loginInfo.setUserDO(detail);
        return loginInfo;
    }

    @Override
    public void logout() {
        // 仅退出当前token
        Long userId = ReqInfoContextHolder.getReqInfo().getCurrentUser().getUserId();
        String token = ReqInfoContextHolder.getReqInfo().getToken();
        redisClient.sRem(LOGIN_USER + userId, token);
        redisClient.delete(LOGIN_TOKEN + token);
    }

    @Override
    public void sendResetPasswordEmail(AuthDO authDO) {
        UserDO detail = userRepo.selectById(authDO.getUserId());
        if (detail.getEmail() == null) {
            throw new BusinessException(GlobalExceptionCode.UNKNOWN_OTHER, "当前账号未绑定邮箱");
        }
        // 生成验证码，过期时间 5分钟
        String code = CaptchaUtil.generateNumericCode();
        int expire = 5;

        // 发送邮件
        redisClient.set(RESET_PASSWORD_CAPTCHA_KEY + detail.getUserId(), code, expire, TimeUnit.MINUTES);
        mailClient.send(ResetPasswordCodeTemplate.getInstance(code, expire), detail.getEmail());
    }

    @Override
    public void resetPassword(AuthDO authDO) {
        UserDO detail = userRepo.selectById(authDO.getUserId());
        // 校验验证码
        String sendCode = (String) redisClient.get(RESET_PASSWORD_CAPTCHA_KEY + detail.getUserId());
        if (!authDO.getCode().equals(sendCode)) {
            throw new BusinessException(LoginExceptionCode.CODE_NOT_MATCH);
        }
        redisClient.delete(RESET_PASSWORD_CAPTCHA_KEY + detail.getUserId());

        // 更新密码
        UserDO userDO = new UserDO();
        userDO.setUserId(detail.getUserId());
        userDO.setPassword(EncryptUtil.md5(authDO.getPassword()));
        userRepo.updateById(userDO);
    }

    @Override
    public void sendResetEmailEmail(AuthDO authDO) {
        UserDO detail = userRepo.selectById(authDO.getUserId());
        if (authDO.getEmail() == null) {
            throw new BusinessException(GlobalExceptionCode.UNKNOWN_OTHER, "请输入邮箱");
        }
        if (authDO.getEmail().equals(detail.getEmail())) {
            throw new BusinessException(GlobalExceptionCode.UNKNOWN_OTHER, "与目前邮箱相同");
        }
        // 生成验证码，过期时间 5分钟
        String code = CaptchaUtil.generateNumericCode();
        int expire = 5;

        // 发送邮件
        redisClient.set(RESET_EMAIL_CAPTCHA_KEY + authDO.getEmail(), code, expire, TimeUnit.MINUTES);
        mailClient.send(ResetEmailCodeTemplate.getInstance(code, expire), authDO.getEmail());
    }

    @Override
    public void resetEmail(AuthDO authDO) {
        UserDO detail = userRepo.selectById(authDO.getUserId());
        // 校验验证码
        String sendCode = (String) redisClient.get(RESET_EMAIL_CAPTCHA_KEY + authDO.getEmail());
        if (!authDO.getCode().equals(sendCode)) {
            throw new BusinessException(LoginExceptionCode.CODE_NOT_MATCH);
        }
        redisClient.delete(RESET_EMAIL_CAPTCHA_KEY + authDO.getEmail());

        // 更新邮箱
        UserDO userDO = new UserDO();
        userDO.setUserId(detail.getUserId());
        userDO.setEmail(authDO.getEmail());
        userRepo.updateById(userDO);
    }

    /**
     * MD5 加密
     */
    public static void main(String[] args) {
        String rawPassword = "123456";
        String encodedPassword = EncryptUtil.md5(rawPassword);
        System.out.println("rawPassword = " + rawPassword);
        System.out.println("encodedPassword = " + encodedPassword);
    }

}
