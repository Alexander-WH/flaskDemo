-- 1. 创建数据库
CREATE DATABASE IF NOT EXISTS test DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE test;

-- 2. 创建 user 表
CREATE TABLE IF NOT EXISTS `user` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(28) NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` tinyint(1) NOT NULL,
  `sex` tinyint(1) DEFAULT NULL,
  `telephone` varchar(255) NOT NULL,
  `address` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `telephone` (`telephone`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. 初始化管理员账号
-- 注意：这里的密码是明文 123456 经过 MD5 加盐后的结果（对应你 flaskDemo 里 MD5_SALT = "test2020#%*"）
-- 如果 SALT 变了，这个密码就失效了。也可以留空，通过 /register 接口注册。
INSERT INTO `user` (`id`, `username`, `password`, `role`, `sex`, `telephone`, `address`)
VALUES (1, 'wintest5', '3aaae25f3dad0de8b4d1efe7a31b9932', 0, 0, '13800138000', '北京市');
-- 注意：上面密码这段，用户可以自己注册然后手动 update role=0。