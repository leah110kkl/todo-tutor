FROM 192.168.0.20:80/library/openjdk:8

# 添加时区环境变量，亚洲，上海
ENV TimeZone=Asia/Shanghai
# 使用软连接，并且将时区配置覆盖/etc/timezone
RUN ln -snf /usr/share/zoneinfo/$TimeZone /etc/localtime && echo $TimeZone > /etc/timezone

# 将jar包复制到容器中
ADD target/backend-java-1.0.0.jar /backend-java.jar
# 启动
ENTRYPOINT ["java","-jar","/backend-java.jar"]