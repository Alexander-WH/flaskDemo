# flaskDemo

本项目是一个基于 **Python + Flask + MySQL + Redis** 开发的简单后端接口项目。实现了用户注册、登录、增删改查等核心功能，采用 Token 鉴权机制与基于角色的权限控制（RBAC）。

目前为纯后端接口，暂无前端界面，可通过 Postman、Jmeter、Apifox 等工具请求测试。

> 配套接口自动化测试项目（Pytest + Requests + Allure）：[pytestDemo](https://github.com/Alexander-WH/pytestDemo)

## 技术选型

- **Web 框架**：Flask
- **关系型数据库**：MySQL（存储用户信息）
- **NoSQL 缓存**：Redis（存储用户 Token，支持过期时间）
- **数据库驱动**：PyMySQL（已采用参数化查询，防止 SQL 注入）
- **安全加密**：MD5 加盐加密（密码存储、Token 生成）
- **鉴权机制**：自定义装饰器 + Redis Token 校验

## 项目结构

- `api/`：接口路由层（Controller）
  - `user.py`：用户模块接口
- `common/`：公共工具类（业务逻辑与数据访问）
  - `mysql_operate.py`：MySQL 数据库连接与操作封装
  - `redis_operate.py`：Redis 连接与 Token 操作封装
  - `md5_operate.py`：MD5 加密工具
- `config/`：配置文件夹
  - `setting.example.py`：配置文件模板（上传至Git）
  - `setting.py`：本地真实配置文件（已被.gitignore忽略）
- `init.sql`：数据库初始化脚本
- `generate_data.py`：批量造数脚本（用于生成测试数据）
- `app.py`：项目启动入口文件
- `requirements.txt`：项目依赖清单

## 环境要求

- Python 3.8+（推荐 3.10 或 3.11，对于3.12+ 也做了适配版本自行测试）
- MySQL 5.7+ 或 8.0
- Redis 服务（默认端口 6379）

## 项目部署

### 1. 下载与安装依赖

下载项目源码后，在根目录下执行以下命令安装依赖：

```bash
pip install -r requirements.txt
```

### 2. 初始化数据库

在 MySQL 中创建数据库并建表。你可以直接在 DBeaver/Navicat 中执行根目录下的 **init.sql** 脚本，或者通过命令行执行：

```bash
mysql -u root -p < init.sql
```

*(注：该脚本会自动创建 test 数据库、user 表，并初始化一个管理员账号)*

### 3. 修改项目配置

1. 进入 `config/` 文件夹，复制 `setting.example.py`，并重命名为 `setting.py`。
2. 打开 `setting.py`，填入你本机的 MySQL 密码和 Redis 密码。

```python
# MySQL配置
MYSQL_PASSWD = "your_mysql_password_here"
# Redis配置
REDIS_PASSWD = "your_redis_password_here"
```

*(注意：如果你的 Redis 没有密码，请将 REDIS_PASSWD 设为 None 或空字符串)*

### 4. 启动项目

**本地开发环境 (Windows/Mac)**
在 PyCharm 终端或命令行直接运行：

```bash
python app.py
```

启动成功后，接口地址默认为 `http://127.0.0.1:9999`。

**生产环境部署 (Linux)**
在 Linux 服务器上，建议使用 `nohup` 让程序在后台运行：

```bash
# /path/to/flaskDemo/app.py 表示项目根路径下的 app.py 启动入口文件路径
# /path/to/flaskDemo/flaskDemo.log 表示输出的日志文件路径
nohup python3 /path/to/flaskDemo/app.py >/path/to/flaskDemo/flaskDemo.log 2>&1 &
```

## 数据库设计

`user` 表各字段对应含义如下：

| 字段名       | 类型           | 描述   | 备注           |
| --------- | ------------ | ---- | ------------ |
| id        | int(11)      | 用户ID | 主键，自增长       |
| username  | varchar(20)  | 用户名  | 唯一           |
| password  | varchar(255) | 密码   | MD5加盐加密后存储   |
| role      | tinyint(1)   | 用户角色 | 0=管理员，1=普通用户 |
| sex       | tinyint(1)   | 性别   | 0=男，1=女，允许为空 |
| telephone | varchar(255) | 手机号  | 唯一，用于登录或注册   |
| address   | varchar(255) | 联系地址 | 允许为空         |

## 接口请求示例

> 默认初始化管理员账号：`wintest5` / `123456`（如无法登录，请通过 /register 接口自行注册并手动修改 role=0）。

- **获取所有用户**：

```
请求方式：GET
请求地址：http://127.0.0.1:9999/users
```

- **获取某个用户信息**：

```
请求方式：GET
请求地址：http://127.0.0.1:9999/users/wintest5
```

- **用户注册**：

```
请求方式：POST
请求地址：http://127.0.0.1:9999/register
请求头：Content-Type: application/json

Body：
{
  "username": "wintest5",
  "password": "123456",
  "sex": "1",
  "telephone": "13500010005",
  "address": "上海市黄浦区"
}
```

- **用户登录**（获取 Token）：

```
请求方式：POST
请求地址：http://127.0.0.1:9999/login
请求头：Content-Type: application/x-www-form-urlencoded 或 application/json

Body：
username=wintest5&password=123456
```

- **修改用户信息**（需携带管理员权限的 Token）：

```text
请求方式：PUT
请求地址：http://127.0.0.1:9999/update/user/3
请求头：Content-Type: application/json

Body：
{
  "admin_user": "wintest5",
  "token": "登录返回的Token",
  "password": "12345678",
  "sex": "1",
  "telephone": "13500010003",
  "address": "广州市天河区"
}
```

- **删除用户**（需携带管理员权限的 Token）：

```
请求方式：POST
请求地址：http://127.0.0.1:9999/delete/user/test
请求头：Content-Type: application/json

Body：
{
  "admin_user": "wintest5",
  "token": "登录返回的Token"
}
```
