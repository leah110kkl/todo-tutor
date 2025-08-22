package cloud.abaaba.controller;

import cloud.abaaba.common.exception.Response;
import cloud.abaaba.common.trace.ReqInfoContextHolder;
import cloud.abaaba.controller.dto.AuthDTO;
import cloud.abaaba.service.AuthService;
import cloud.abaaba.service.domain.AuthDO;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.annotation.Resource;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * AuthController
 *
 * @author Pig-Gua
 * @date 2025-05-27
 */
@RestController
@RequestMapping("/auth")
@Tag(name = "用户认证")
public class AuthController {

    @Resource
    private AuthService authService;

    /**
     * 登录（用户名+密码）
     */
    @Operation(summary = "用户名密码登录")
    @PostMapping("/loginByUsername")
    public Response<AuthDO> loginByUsername(@RequestBody AuthDTO loginDTO) {
        return Response.success(authService.loginByUsername(loginDTO));
    }

    /**
     * 登录场景-发送邮箱验证码
     */
    @Operation(summary = "发送验证码（邮箱登录）")
    @PostMapping("/sendLoginEmail")
    public Response<?> sendLoginEmail(@RequestBody AuthDTO loginDTO) {
        authService.sendLoginEmail(loginDTO);
        return Response.success();
    }

    /**
     * 登录（邮箱+验证码）
     */
    @Operation(summary = "邮箱验证码登录")
    @PostMapping("/loginByEmail")
    public Response<AuthDO> loginByEmail(@RequestBody AuthDTO loginDTO) {
        return Response.success(authService.loginByEmail(loginDTO));
    }

    /**
     * 登出
     */
    @Operation(summary = "退出登录")
    @PostMapping("/logout")
    public Response<?> logout() {
        authService.logout();
        return Response.success();
    }

    @Operation(summary = "发送验证码（重置密码）")
    @PostMapping("/sendResetPasswordEmail")
    public Response<?> sendResetPasswordEmail() {
        // 上下文中获取当前用户ID
        Long userId = ReqInfoContextHolder.getReqInfo().getCurrentUser().getUserId();
        AuthDTO loginDTO = new AuthDTO();
        loginDTO.setUserId(userId);

        // 发送重置密码邮件
        authService.sendResetPasswordEmail(loginDTO);
        return Response.success();
    }

    @Operation(summary = "重置密码")
    @PostMapping("/resetPassword")
    public Response<?> resetPassword(@RequestBody AuthDTO loginDTO) {
        // 上下文中获取当前用户ID
        Long userId = ReqInfoContextHolder.getReqInfo().getCurrentUser().getUserId();
        loginDTO.setUserId(userId);

        // 重置密码
        authService.resetPassword(loginDTO);
        return Response.success();
    }

    @Operation(summary = "发送验证码（换绑邮箱）")
    @PostMapping("/sendResetEmailEmail")
    public Response<?> sendResetEmailEmail(@RequestBody AuthDTO loginDTO) {
        // 上下文中获取当前用户ID
        Long userId = ReqInfoContextHolder.getReqInfo().getCurrentUser().getUserId();
        loginDTO.setUserId(userId);

        // 发送重置密码邮件
        authService.sendResetEmailEmail(loginDTO);
        return Response.success();
    }

    @Operation(summary = "换绑邮箱")
    @PostMapping("/resetEmail")
    public Response<?> resetEmail(@RequestBody AuthDTO loginDTO) {
        // 上下文中获取当前用户ID
        Long userId = ReqInfoContextHolder.getReqInfo().getCurrentUser().getUserId();
        loginDTO.setUserId(userId);

        // 重置密码
        authService.resetEmail(loginDTO);
        return Response.success();
    }

}
