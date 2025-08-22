package cloud.abaaba.common.mail;

import cn.hutool.core.collection.CollectionUtil;
import cn.hutool.core.util.StrUtil;
import cloud.abaaba.common.exception.BusinessException;
import cloud.abaaba.common.exception.enums.MailExceptionCode;
import jakarta.mail.internet.InternetAddress;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.MimeMessageHelper;
import org.springframework.stereotype.Component;

import java.io.File;
import java.util.Date;
import java.util.List;

/**
 * MailClient
 *
 * @author Pig-Gua
 * @date 2025-05-29
 */
@Slf4j
@Component
public class MailClient {

    @Autowired
    private JavaMailSender mailSender;

    public void send(MailTemplate mailTemplate, String to) {
        this.send("Todo Tutor", "1270701867@qq.com", to, mailTemplate.getSubject(), mailTemplate.getContent(), mailTemplate.isHtml(), null, null, null);
    }

    public void send(String name, String from, String to, String subject, String content, Boolean isHtml, String cc, String bcc, List<File> files) {

        if (StrUtil.hasBlank(from, to, subject, content)) {
            throw new BusinessException(MailExceptionCode.PARAM_NOT_NULL, "发送人,接收人,主题,内容");
        }

        try {
            //true表示支持复杂类型
            MimeMessageHelper messageHelper = new MimeMessageHelper(mailSender.createMimeMessage(), true);
            //邮件发信人
            messageHelper.setFrom(new InternetAddress(from, name));
            //邮件收信人
            messageHelper.setTo(to.split(","));
            //邮件主题
            messageHelper.setSubject(subject);
            //邮件内容
            messageHelper.setText(content, isHtml);
            //抄送
            if (!StrUtil.isEmpty(cc)) {
                messageHelper.setCc(cc.split(","));
            }
            //密送
            if (!StrUtil.isEmpty(bcc)) {
                messageHelper.setCc(bcc.split(","));
            }
            //添加邮件附件
            if (CollectionUtil.isNotEmpty(files)) {
                for (File file : files) {
                    messageHelper.addAttachment(file.getName(), file);
                }
            }
            // 邮件发送时间
            messageHelper.setSentDate(new Date());
            //正式发送邮件
            mailSender.send(messageHelper.getMimeMessage());
        } catch (Exception e) {
            log.error("邮件发送失败", e);
            throw new BusinessException(MailExceptionCode.SEND_ERROR);
        }
    }

}
