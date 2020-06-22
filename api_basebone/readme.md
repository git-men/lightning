### 1 2020-06-19 管理端接口添加权限

添加人：Allen

业务描述：管理端细致到用户对每个接口有没有对应的权限进行操作

在 settings.py 文件中添加对应的配置进行设置

```python
BASEBONE_API_SERVICE = {
    ... # 管理端是否开启接口权限校验
    MANAGE_API_PERMISSION_VALIDATE_ENABLE = True | False
    ...
}
```

使用此开关是否启用接口权限校验

每个接口权限是根据

```python

通用的命名

basebone_api_model_{接口方法名称 | 云函数名称} 格式进行命名

如果是云函数

basebone_api_model_func_{云函数名称} 格式进行命名
```
