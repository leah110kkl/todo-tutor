package cloud.abaaba.common.mybatis;

import com.baomidou.mybatisplus.annotation.DbType;
import com.baomidou.mybatisplus.core.config.GlobalConfig;
import com.baomidou.mybatisplus.core.toolkit.GlobalConfigUtils;
import com.baomidou.mybatisplus.extension.plugins.MybatisPlusInterceptor;
import com.baomidou.mybatisplus.extension.plugins.inner.PaginationInnerInterceptor;
import com.baomidou.mybatisplus.extension.spring.MybatisSqlSessionFactoryBean;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.io.Resource;
import org.springframework.core.io.support.PathMatchingResourcePatternResolver;

import javax.sql.DataSource;
import java.io.IOException;

/**
 * MyBatisPlusConfiguration
 *
 * @author Pig-Gua
 * @date 2025-05-27
 */
@Configuration
public class MyBatisPlusConfiguration {

    /**
     * myBatisSqlSessionFactoryBean
     *
     * @param dataSource             数据源
     * @param mybatisPlusInterceptor 插件
     * @return factoryBean
     */
    @Bean("sqlSessionFactory")
    public MybatisSqlSessionFactoryBean sqlSessionFactory(DataSource dataSource, MybatisPlusInterceptor mybatisPlusInterceptor) {
        MybatisSqlSessionFactoryBean sqlSessionFactoryBean = new MybatisSqlSessionFactoryBean();
        // 数据源
        sqlSessionFactoryBean.setDataSource(dataSource);

        // mapper
        Resource[] resources = null;
        try {
            resources = new PathMatchingResourcePatternResolver().getResources("classpath*:mapper/*.xml");
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
        sqlSessionFactoryBean.setMapperLocations(resources);

        //全局配置
        GlobalConfig globalConfig = GlobalConfigUtils.defaults();
        globalConfig.setMetaObjectHandler(new DefaultMetaObjectHandler());
        sqlSessionFactoryBean.setGlobalConfig(globalConfig);

        // 插件列表：分页插件
        sqlSessionFactoryBean.setPlugins(mybatisPlusInterceptor);
        return sqlSessionFactoryBean;
    }

    /**
     * myBatisPlus 分页插件
     */
    @Bean
    public MybatisPlusInterceptor mybatisPlusInterceptor() {
        MybatisPlusInterceptor mybatisPlusInterceptor = new MybatisPlusInterceptor();
        mybatisPlusInterceptor.addInnerInterceptor(new PaginationInnerInterceptor(DbType.MYSQL));
        return mybatisPlusInterceptor;
    }

}
