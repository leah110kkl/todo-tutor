package cloud.abaaba.common.trace;

import cloud.abaaba.service.domain.UserDO;
import lombok.Data;

/**
 * ReqInfo 请求信息
 *
 * @author Pig-Gua
 * @date 2025-05-24
 */
@Data
public class ReqInfo {

    /**
     * 链路ID
     */
    private String traceId;

    /**
     * 当前用户 token
     */
    private String token;

    /**
     * 当前用户
     */
    private UserDO currentUser;

}
