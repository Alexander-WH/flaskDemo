# ==================== 兼容 Python 3.12+ 的补丁 ====================
import pkgutil
import importlib.util

if not hasattr(pkgutil, 'get_loader'):
    def _get_loader(name):
        spec = importlib.util.find_spec(name)
        return spec.loader if spec else None

    pkgutil.get_loader = _get_loader
# =====================================================================

from flask import Flask, jsonify, request
from common.mysql_operate import db
from common.redis_operate import redis_db
from common.md5_operate import get_md5
import re
import time
from functools import wraps

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False  # 兼容老版本 Flask


# ==================== 装饰器：验证管理员身份 ====================
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 兼容 JSON 和表单格式，防止 request.json 为空时报错
        if request.is_json:
            data = request.get_json()
        else:
            data = request.values

        admin_user = data.get("admin_user", "").strip()
        token = data.get("token", "").strip()

        if not admin_user or not token:
            return jsonify({"code": 4001, "msg": "管理员用户/token口令不能为空，请检查！！！"})

        redis_token = redis_db.handle_redis_token(admin_user)
        if not redis_token:
            return jsonify({"code": 4002, "msg": "当前用户未登录，请检查！！！"})

        if redis_token != token:
            return jsonify({"code": 4003, "msg": "token口令不正确，请检查！！！"})

        # 查询用户角色
        sql_user_role = "SELECT role FROM user WHERE username = %s"
        res_role = db.select_db(sql_user_role, (admin_user,))
        if not res_role or res_role[0]["role"] != 0:
            return jsonify({"code": 4004, "msg": "当前用户不是管理员用户，无法进行操作，请检查！！！"})

        # 将 admin_user 传递给路由函数使用
        kwargs['admin_user'] = admin_user
        return f(*args, **kwargs)

    return decorated_function


# ==================== 路由 ====================
@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route("/users", methods=["GET"])
def get_all_users():
    """获取所有用户信息"""
    try:
        sql = "SELECT * FROM user"
        data = db.select_db(sql)
        return jsonify({"code": 0, "data": data, "msg": "查询成功"})
    except Exception as e:
        return jsonify({"code": 500, "msg": f"数据库查询异常: {str(e)}"})


@app.route("/users/<string:username>", methods=["GET"])
def get_user(username):
    """获取某个用户信息"""
    try:
        sql = "SELECT * FROM user WHERE username = %s"
        data = db.select_db(sql, (username,))
        if data:
            return jsonify({"code": 0, "data": data, "msg": "查询成功"})
        return jsonify({"code": "1004", "msg": "查不到相关用户的信息"})
    except Exception as e:
        return jsonify({"code": 500, "msg": f"数据库查询异常: {str(e)}"})


@app.route("/register", methods=['POST'])
def user_register():
    """注册用户"""
    data = request.json or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    sex = data.get("sex", "0").strip()
    telephone = data.get("telephone", "").strip()
    address = data.get("address", "").strip()

    if not (username and password and telephone):
        return jsonify({"code": 2001, "msg": "用户名/密码/手机号不能为空，请检查！！！"})

    if sex not in ("0", "1"):
        return jsonify({"code": 2003, "msg": "输入的性别只能是 0(男) 或 1(女)！！！"})

    if not (len(telephone) == 11 and re.match(r"^1[3,5,7,8]\d{9}$", telephone)):
        return jsonify({"code": 2004, "msg": "手机号格式不正确！！！"})

    try:
        sql_check_user = "SELECT username FROM user WHERE username = %s"
        res_user = db.select_db(sql_check_user, (username,))
        if res_user:
            return jsonify({"code": 2002, "msg": "用户名已存在，注册失败！！！"})

        sql_check_tel = "SELECT telephone FROM user WHERE telephone = %s"
        res_tel = db.select_db(sql_check_tel, (telephone,))
        if res_tel:
            return jsonify({"code": 2005, "msg": "手机号已被注册！！！"})

        hashed_password = get_md5(username, password)
        sql_insert = "INSERT INTO user(username, password, role, sex, telephone, address) VALUES(%s, %s, '1', %s, %s, %s)"
        db.execute_db(sql_insert, (username, hashed_password, sex, telephone, address))

        return jsonify({"code": 0, "msg": "恭喜，注册成功！"})
    except Exception as e:
        return jsonify({"code": 500, "msg": f"注册异常: {str(e)}"})


@app.route("/login", methods=['POST'])
def user_login():
    """登录用户"""
    # 【修改处】兼容 JSON 和表单两种格式
    if request.is_json:
        data = request.get_json()
    else:
        data = request.values

    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not (username and password):
        return jsonify({"code": 1001, "msg": "用户名或密码不能为空！！！"})

    try:
        sql_check = "SELECT * FROM user WHERE username = %s"
        res_user = db.select_db(sql_check, (username,))
        if not res_user:
            return jsonify({"code": 1003, "msg": "用户名不存在！！！"})

        hashed_password = get_md5(username, password)
        sql_login = "SELECT * FROM user WHERE username = %s AND password = %s"
        res_login = db.select_db(sql_login, (username, hashed_password))

        if res_login:
            time_stamp = int(time.time())
            token = get_md5(username, str(time_stamp))
            redis_db.handle_redis_token(username, token)

            login_info = {
                "id": res_login[0]["id"],
                "username": username,
                "token": token,
                "login_time": time.strftime("%Y/%m/%d %H:%M:%S")
            }
            return jsonify({"code": 0, "login_info": login_info, "msg": "恭喜，登录成功！"})

        return jsonify({"code": 1002, "msg": "用户名或密码错误！！！"})
    except Exception as e:
        return jsonify({"code": 500, "msg": f"登录异常: {str(e)}"})


@app.route("/update/user/<int:id>", methods=['PUT'])
@admin_required
def user_update(id, admin_user):
    """修改用户信息"""
    if request.is_json:
        data = request.get_json()
    else:
        data = request.values

    new_password = data.get("password", "").strip()
    new_sex = data.get("sex", "0").strip()
    new_telephone = data.get("telephone", "").strip()
    new_address = data.get("address", "").strip()

    if not (new_password and new_telephone):
        return jsonify({"code": 4001, "msg": "密码/手机号不能为空，请检查！！！"})

    if new_sex not in ("0", "1"):
        return jsonify({"code": 4007, "msg": "输入的性别只能是 0(男) 或 1(女)！！！"})

    if not (len(new_telephone) == 11 and re.match(r"^1[3,5,7,8]\d{9}$", new_telephone)):
        return jsonify({"code": 4008, "msg": "手机号格式不正确！！！"})

    try:
        sql_check_id = "SELECT * FROM user WHERE id = %s"
        res_id = db.select_db(sql_check_id, (id,))
        if not res_id:
            return jsonify({"code": 4005, "msg": "修改的用户ID不存在，无法进行修改，请检查！！！"})

        sql_check_tel = "SELECT telephone FROM user WHERE telephone = %s"
        res_tel = db.select_db(sql_check_tel, (new_telephone,))
        if res_tel:
            return jsonify({"code": 4006, "msg": "手机号已被注册，无法进行修改，请检查！！！"})

        if not new_address:
            new_address = res_id[0]["address"]

        hashed_password = get_md5(res_id[0]["username"], new_password)
        sql_update = "UPDATE user SET password = %s, sex = %s, telephone = %s, address = %s WHERE id = %s"
        db.execute_db(sql_update, (hashed_password, new_sex, new_telephone, new_address, id))

        return jsonify({"code": 0, "msg": "恭喜，修改用户信息成功！"})
    except Exception as e:
        return jsonify({"code": 500, "msg": f"修改异常: {str(e)}"})


@app.route("/delete/user/<string:username>", methods=['POST'])
@admin_required
def user_delete(username, admin_user):
    """删除用户"""
    try:
        sql_check = "SELECT * FROM user WHERE username = %s"
        res_user = db.select_db(sql_check, (username,))

        if not res_user:
            return jsonify({"code": 3005, "msg": "删除的用户名不存在，无法进行删除，请检查！！！"})

        if res_user[0]["role"] == 0:
            return jsonify({"code": 3006, "msg": f"用户名：【 {username} 】，该用户不允许删除！！！"})

        sql_delete = "DELETE FROM user WHERE username = %s"
        db.execute_db(sql_delete, (username,))

        return jsonify({"code": 0, "msg": "恭喜，删除用户信息成功！"})
    except Exception as e:
        return jsonify({"code": 500, "msg": f"删除异常: {str(e)}"})


if __name__ == '__main__':
    # 注意：你平时是通过 app.py 启动的，它导入这个 app。
    # 这里直接运行的话端口是 5000，建议统一用 app.py 的 9999 端口启动。
    app.run(host='127.0.0.1', port=5000, debug=True)