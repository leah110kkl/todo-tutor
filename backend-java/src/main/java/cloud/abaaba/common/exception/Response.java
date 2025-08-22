package cloud.abaaba.common.exception;


import cloud.abaaba.common.exception.enums.GlobalExceptionCode;
import lombok.Data;

/**
 * Response 全局通用返回
 *
 * @author Pig-Gua
 * @date 2025-05-24
 */
@Data
public class Response<T> {

    private String code;

    private String msg;

    private T data;

    public static <T> Response<T> success() {
        return Response.success(null);
    }

    public static <T> Response<T> success(T data) {
        return Response.error(GlobalExceptionCode.SUCCESS, data);
    }

    public static <T> Response<T> error(ExceptionCode exceptionCode) {
        return Response.error(exceptionCode, null);
    }

    public static <T> Response<T> error(ExceptionCode exceptionCode, T data) {
        Response<T> result = new Response<>();
        result.code = exceptionCode.getCode();
        result.msg = exceptionCode.getMsg();
        result.data = data;
        return result;
    }

}
