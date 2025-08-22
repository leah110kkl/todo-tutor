package cloud.abaaba.common.exception;

/**
 * ExceptionCode 异常码
 *
 * @author Pig-Gua
 * @date 2025-05-24
 */
public interface ExceptionCode {

    /**
     * 获取错误码
     *
     * @return 错误码
     */
    String getCode();

    /**
     * 获取错误信息
     *
     * @return 错误信息
     */
    String getMsg();

}
