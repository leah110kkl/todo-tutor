package cloud.abaaba.repo.po;

import cloud.abaaba.common.mybatis.BasePO;
import cloud.abaaba.service.constant.UserTypeConstant;
import cloud.abaaba.service.domain.UserDO;
import cn.hutool.core.bean.BeanUtil;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.NoArgsConstructor;

/**
 * UserPO
 *
 * @author Pig-Gua
 * @date 2025-05-27
 */
@Data
@EqualsAndHashCode(callSuper = true)
@AllArgsConstructor
@NoArgsConstructor
@TableName("tb_user")
public class UserPO extends BasePO {

    /**
     * 昵称
     */
    private String nickName;

    /**
     * 头像地址
     */
    private String avatarUrl;

    /**
     * 用户名
     */
    private String username;

    /**
     * 邮箱
     */
    private String email;

    /**
     * 密码
     */
    private String password;

    /**
     * 用户类型：0-匿名用户 1-普通用户
     *
     * @see UserTypeConstant
     */
    private String type;

    public UserPO(UserDO userDO) {
        BeanUtil.copyProperties(userDO, this);
        this.setId(userDO.getUserId());
    }

    public UserDO toDO() {
        UserDO userDO = BeanUtil.copyProperties(this, UserDO.class);
        userDO.setUserId(this.getId());
        return userDO;
    }

}
