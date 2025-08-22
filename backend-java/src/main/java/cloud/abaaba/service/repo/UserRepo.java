package cloud.abaaba.service.repo;

import cloud.abaaba.service.domain.UserDO;
import com.baomidou.mybatisplus.core.metadata.IPage;

import java.util.List;

/**
 * UserRepo
 *
 * @author Pig-Gua
 * @date 2025-05-27
 */
public interface UserRepo {

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
     * 详情查询
     *
     * @param userId 查询条件
     * @return detail
     */
    UserDO selectById(Long userId);

    /**
     * 详情查询
     *
     * @param username 查询条件
     * @return detail
     */
    UserDO selectByUsername(String username);

    /**
     * 详情查询
     *
     * @param email 查询条件
     * @return detail
     */
    UserDO selectByEmail(String email);

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
