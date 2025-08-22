package cloud.abaaba.repo.mapper;

import cloud.abaaba.repo.po.UserPO;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.apache.ibatis.annotations.Mapper;

/**
 * UserMapper
 *
 * @author Pig-Gua
 * @date 2025-05-27
 */
@Mapper
public interface UserMapper extends BaseMapper<UserPO> {
}
