package cloud.abaaba.common.exception.enums;

import cloud.abaaba.common.exception.ExceptionCode;
import lombok.AllArgsConstructor;
import lombok.Getter;

@Getter
@AllArgsConstructor
public enum ConversationExceptionCode implements ExceptionCode {

    CONVERSATION_NOT_FOUND("", "未找到会话内容"),
    USER_MESSAGE_NOT_FOUND("", "用户信息不能为空");

    /**
     * 错误码
     */
    private final String code;

    /**
     * 错误信息
     */
    private final String msg;

}
