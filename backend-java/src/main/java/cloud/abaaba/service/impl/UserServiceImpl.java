package cloud.abaaba.service.impl;

import cloud.abaaba.common.exception.BusinessException;
import cloud.abaaba.common.exception.enums.GlobalExceptionCode;
import cloud.abaaba.common.utils.EncryptUtil;
import cloud.abaaba.service.UserService;
import cloud.abaaba.service.domain.UserDO;
import cloud.abaaba.service.repo.UserRepo;
import cn.hutool.core.util.StrUtil;
import com.baomidou.mybatisplus.core.metadata.IPage;
import jakarta.annotation.Resource;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * UserServiceImpl
 *
 * @author Pig-Gua
 * @date 2025-05-27
 */
@Service
public class UserServiceImpl implements UserService {

    @Resource
    private UserRepo userRepo;

    /**
     * 新用户默认密码
     */
    public static final String DEFAULT_PASSWORD = "123456";

    @Override
    public IPage<UserDO> page(UserDO userDO, Integer pageNum, Integer pageSize) {
        return userRepo.page(userDO, pageNum, pageSize);
    }

    @Override
    public List<UserDO> list(UserDO userDO) {
        return userRepo.list(userDO);
    }

    @Override
    public UserDO detail(UserDO userDO) {
        return userRepo.selectById(userDO.getUserId());
    }

    @Override
    public Long insert(UserDO userDO) {
        List<UserDO> list = userRepo.list(new UserDO());
        if (list.stream().anyMatch(item -> item.getUsername().equals(userDO.getUsername()))) {
            throw new BusinessException(GlobalExceptionCode.UNKNOWN_OTHER, "账户名已存在");
        }
        if (StrUtil.isNotBlank(userDO.getEmail()) && list.stream().anyMatch(item -> userDO.getEmail().equals(item.getEmail()))) {
            throw new BusinessException(GlobalExceptionCode.UNKNOWN_OTHER, "邮箱已存在");
        }

        // 设置初始密码
        userDO.setPassword(EncryptUtil.md5(DEFAULT_PASSWORD));
        return userRepo.insert(userDO);
    }

    @Override
    public Long updateById(UserDO userDO) {
        UserDO detail = userRepo.selectById(userDO.getUserId());
        List<UserDO> list = userRepo.list(new UserDO());
        if (StrUtil.isNotBlank(userDO.getEmail())) {
            List<UserDO> collect = list.stream()
                    .filter(item -> userDO.getEmail().equals(item.getEmail()))
                    .toList();
            if (!collect.isEmpty() && !collect.get(0).getUserId().equals(detail.getUserId())) {
                throw new BusinessException(GlobalExceptionCode.UNKNOWN_OTHER, "邮箱已存在");
            }
        }
        return userRepo.updateById(userDO);
    }

    @Override
    public Long deleteById(UserDO userDO) {
        return userRepo.deleteById(userDO);
    }

}
