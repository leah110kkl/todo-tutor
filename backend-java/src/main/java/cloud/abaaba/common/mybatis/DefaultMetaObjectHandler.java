package cloud.abaaba.common.mybatis;

import com.baomidou.mybatisplus.core.handlers.MetaObjectHandler;
import cloud.abaaba.common.trace.ReqInfoContextHolder;
import org.apache.ibatis.reflection.MetaObject;

import java.util.Date;
import java.util.Objects;

/**
 * DefaultMetaObjectHandler
 *
 * @author Pig-Gua
 * @date 2025-05-27
 */
public class DefaultMetaObjectHandler implements MetaObjectHandler {

    /**
     * 插入元对象字段填充（用于插入时对公共字段的填充）
     * @param metaObject 元对象
     */
    @Override
    public void insertFill(MetaObject metaObject) {
        if (Objects.nonNull(metaObject) && metaObject.getOriginalObject() instanceof BasePO) {
            BasePO basePO = (BasePO) metaObject.getOriginalObject();

            // 删除标志
            basePO.setIsDelete("0");

            // 设置时间
            Date date = new Date();
            basePO.setCreateTime(date);
            basePO.setUpdateTime(date);

            // 设置用户
            Long userId = ReqInfoContextHolder.getReqInfo().getCurrentUser().getUserId();
            basePO.setCreateBy(userId);
            basePO.setUpdateBy(userId);
        }
    }

    /**
     * 更新元对象字段填充（用于更新时对公共字段的填充）
     * @param metaObject 元对象
     */
    @Override
    public void updateFill(MetaObject metaObject) {
        if (Objects.nonNull(metaObject) && metaObject.getOriginalObject() instanceof BasePO) {
            BasePO basePO = (BasePO) metaObject.getOriginalObject();

            // 设置时间
            basePO.setUpdateTime(new Date());

            // 设置用户
            Long userId = ReqInfoContextHolder.getReqInfo().getCurrentUser().getUserId();
            basePO.setUpdateBy(userId);
        }
    }

}
