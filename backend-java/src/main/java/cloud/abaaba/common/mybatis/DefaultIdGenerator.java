package cloud.abaaba.common.mybatis;

import cn.hutool.core.util.IdUtil;
import com.baomidou.mybatisplus.core.incrementer.IdentifierGenerator;
import org.springframework.stereotype.Component;

/**
 * DefaultIdGenerator
 *
 * @author Pig-Gua
 * @date 2025-05-27
 */
@Component
public class DefaultIdGenerator implements IdentifierGenerator {

    @Override
    public Long nextId(Object entity) {
        return IdUtil.getSnowflakeNextId();
    }

}
