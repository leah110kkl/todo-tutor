package cloud.abaaba.common.mail.template;

import cloud.abaaba.common.mail.MailTemplate;
import lombok.Data;

/**
 * ResetEmailCodeTemplate
 *
 * @author Pig-Gua
 * @date 2025-07-24
 */
@Data
public class ResetEmailCodeTemplate implements MailTemplate {

    private String subject = "您正在重置邮箱";

    private String content = "您正在重置邮箱，验证码为：%s，有效期%s分钟。";

    private boolean isHtml = false;


    private ResetEmailCodeTemplate() {
    }

    public static ResetEmailCodeTemplate getInstance(String code, int expire) {
        ResetEmailCodeTemplate template = new ResetEmailCodeTemplate();
        String formatContent = String.format(template.getContent(), code, expire);
        template.setContent(formatContent);
        return template;
    }

}
