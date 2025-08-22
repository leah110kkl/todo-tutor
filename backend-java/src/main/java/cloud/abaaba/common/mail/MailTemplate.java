package cloud.abaaba.common.mail;

/**
 * MailTemplate
 *
 * @author Pig-Gua
 * @date 2025-05-29
 */
public interface MailTemplate {

    /**
     * 获取邮件标题
     *
     * @return 邮件标题
     */
    String getSubject();

    /**
     * 获取邮件内容
     *
     * @return 邮件内容
     */
    String getContent();

    /**
     * 是否是HTML邮件
     *
     * @return 是否是HTML邮件
     */
    boolean isHtml();

}
