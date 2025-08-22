package cloud.abaaba.repo;

import cloud.abaaba.common.utils.ListUtil;
import cloud.abaaba.common.utils.PageUtil;
import cloud.abaaba.repo.mapper.UserMapper;
import cloud.abaaba.repo.po.UserPO;
import cloud.abaaba.service.domain.UserDO;
import cloud.abaaba.service.repo.UserRepo;
import cn.hutool.core.util.StrUtil;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import jakarta.annotation.Resource;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Component;

import java.util.List;

/**
 * UserRepoImpl
 *
 * @author Pig-Gua
 * @date 2025-05-27
 */
@Component
public class UserRepoImpl extends ServiceImpl<UserMapper, UserPO> implements UserRepo {

    @Resource
    private UserMapper userMapper;

    @Override
    public IPage<UserDO> page(UserDO userDO, Integer pageNum, Integer pageSize) {
        LambdaQueryWrapper<UserPO> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.like(StrUtil.isNotBlank(userDO.getUsername()), UserPO::getUsername, userDO.getUsername());
        queryWrapper.like(StrUtil.isNotBlank(userDO.getNickName()), UserPO::getNickName, userDO.getNickName());
        queryWrapper.like(StrUtil.isNotBlank(userDO.getEmail()), UserPO::getEmail, userDO.getEmail());
        Page<UserPO> page = userMapper.selectPage(new Page<>(pageNum, pageSize), queryWrapper);
        return PageUtil.convert(page, UserPO::toDO);
    }

    @Override
    public List<UserDO> list(UserDO userDO) {
        LambdaQueryWrapper<UserPO> queryWrapper = new LambdaQueryWrapper<>();
        List<UserPO> list = userMapper.selectList(queryWrapper);
        return ListUtil.convert(list, UserPO::toDO);
    }

    @Override
    public UserDO selectById(Long userId) {
        UserPO userPO = userMapper.selectById(userId);
        if (userPO == null) {
            return null;
        }
        return userPO.toDO();
    }

    @Override
    public UserDO selectByUsername(String username) {
        LambdaQueryWrapper<UserPO> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(UserPO::getUsername, username);
        UserPO userPO = userMapper.selectOne(queryWrapper);
        if (userPO == null) {
            return null;
        }
        return userPO.toDO();
    }

    @Override
    public UserDO selectByEmail(String email) {
        LambdaQueryWrapper<UserPO> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(UserPO::getEmail, email);
        UserPO userPO = userMapper.selectOne(queryWrapper);
        if (userPO == null) {
            return null;
        }
        return userPO.toDO();
    }

    @Override
    public Long insert(UserDO userDO) {
        userMapper.insert(new UserPO(userDO));
        return userDO.getUserId();
    }

    @Override
    public Long updateById(UserDO userDO) {
        userMapper.updateById(new UserPO(userDO));
        return userDO.getUserId();
    }

    @Override
    public Long deleteById(UserDO userDO) {
        userMapper.deleteById(userDO.getUserId());
        return userDO.getUserId();
    }

}
