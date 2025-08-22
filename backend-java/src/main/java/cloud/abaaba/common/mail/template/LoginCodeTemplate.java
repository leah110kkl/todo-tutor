package cloud.abaaba.common.mail.template;

import cloud.abaaba.common.mail.MailTemplate;
import lombok.Data;

/**
 * LoginCodeTemplate
 *
 * @author Pig-Gua
 * @date 2025-05-29
 */
@Data
public class LoginCodeTemplate implements MailTemplate {

    private String subject = "您正在登录【Todo Tutor】";

    private String content = "您正在登录【Todo Tutor】，验证码为：%s，有效期%s分钟。";

    private boolean isHtml = false;


    private LoginCodeTemplate() {
    }

    public static LoginCodeTemplate getInstance(String code, int expire) {
        LoginCodeTemplate template = new LoginCodeTemplate();
        String formatContent = String.format(template.getContent(), code, expire);
        template.setContent(formatContent);
        return template;
    }

}
