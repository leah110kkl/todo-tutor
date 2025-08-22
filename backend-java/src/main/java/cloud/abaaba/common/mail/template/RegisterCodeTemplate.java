package cloud.abaaba.common.mail.template;

import cloud.abaaba.common.mail.MailTemplate;
import lombok.Data;

/**
 * RegisterCodeTemplate
 *
 * @author Pig-Gua
 * @date 2025-08-22
 */
@Data
public class RegisterCodeTemplate implements MailTemplate {

    private String subject = "您正在注册【Todo Tutor】";

    private String content = "您正在注册【Todo Tutor】，验证码为：%s，有效期%s分钟。";

    private boolean isHtml = false;


    private RegisterCodeTemplate() {
    }

    public static RegisterCodeTemplate getInstance(String code, int expire) {
        RegisterCodeTemplate template = new RegisterCodeTemplate();
        String formatContent = String.format(template.getContent(), code, expire);
        template.setContent(formatContent);
        return template;
    }

}