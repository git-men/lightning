# 通用开发套件最佳实践接口服务层

演示用的例子


## 安装步骤

- 需要安装 python 3.6.x
- pull 代码
- 然后到对应的目录，执行 pip install -r requirements.txt
- 然后到 service 目录。建立 .env 文件，此文件和 settings.py 同级
- 创建数据库，假如数据库名字为 sky
- 修改 .env 文件 添加 DEFAULT_DATABASE=mysql://root:@127.0.0.1:3306/sky(注意，这里是数据库名字)
- 然后到 shell 环境，引用 serivce 下面的 fake.py 中的 create_data 方法，执行此方法
- 运行服务

## 其他

### 使用阿里云 OSS 的上传服务

则在 .env 文件中，添加以下配置，具体参数找我们的 Boss 要，下面的参数只是演示；

```python
ALI_YUN_OSS_KEY=xxxxx
ALI_YUN_OSS_SECRET=xxxxxxxx
ALI_YUN_OSS_ENDPOINT=oss-cn-beijing.aliyuncs.com
ALI_YUN_OSS_HOST=http://vinyl.oss-cn-beijing.aliyuncs.com
ALI_YUN_OSS_BUCKET=vinyl
```
