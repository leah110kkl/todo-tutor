package cloud.abaaba.service;

import cloud.abaaba.service.domain.UserDO;
import com.baomidou.mybatisplus.core.metadata.IPage;

import java.util.List;

/**
 * UserService
 *
 * @author Pig-Gua
 * @date 2025-05-27
 */
public interface UserService {

    /**
     * 分页查询
     *
     * @param userDO   查询条件
     * @param pageNum  当前页
     * @param pageSize 页大小
     * @return page
     */
    IPage<UserDO> page(UserDO userDO, Integer pageNum, Integer pageSize);

    /**
     * 列表查询
     *
     * @param userDO   查询条件
     * @return list
     */
    List<UserDO> list(UserDO userDO);

    /**
     * 详情
     *
     * @param userDO userDO
     * @return detail
     */
    UserDO detail(UserDO userDO);

    /**
     * 新增
     *
     * @param userDO userDO
     * @return 主键ID
     */
    Long insert(UserDO userDO);

    /**
     * 修改
     *
     * @param userDO userDO
     * @return 主键ID
     */
    Long updateById(UserDO userDO);

    /**
     * 删除
     *
     * @param userDO userDO
     * @return 主键ID
     */
    Long deleteById(UserDO userDO);

}
