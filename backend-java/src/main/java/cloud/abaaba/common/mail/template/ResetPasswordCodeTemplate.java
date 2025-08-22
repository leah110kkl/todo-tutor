package cloud.abaaba.common.mail.template;

import cloud.abaaba.common.mail.MailTemplate;
import lombok.Data;

/**
 * ResetPasswordCodeTemplate
 *
 * @author Pig-Gua
 * @date 2025-07-24
 */
@Data
public class ResetPasswordCodeTemplate implements MailTemplate {

    private String subject = "您正在重置密码";

    private String content = "您正在重置密码，验证码为：%s，有效期%s分钟。";

    private boolean isHtml = false;


    private ResetPasswordCodeTemplate() {
    }

    public static ResetPasswordCodeTemplate getInstance(String code, int expire) {
        ResetPasswordCodeTemplate template = new ResetPasswordCodeTemplate();
        String formatContent = String.format(template.getContent(), code, expire);
        template.setContent(formatContent);
        return template;
    }

}
