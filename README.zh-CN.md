


<!-- PROJECT LOGO -->
<br />
<p align="center">


  <h3 align="center">Lightning -- 基于Django的无代码Admin以及低代码Web开发框架</h3>

  <p align="center">

    
  </p>
</p>


<!-- ABOUT THE PROJECT -->
## 关于项目

lightning 是闪电数据管理社区开源版，是一个无代码的Admin和低代码Web开发框架, 适用于Django开发者。
    
你只需要编写业务模型代码，lightning 一键为你生成Admin，通过在线页面配置面板，可实时调整Admin页面功能，无需重新部署。

lightning 还是一个适用于web的低代码开发框架, 通过它可以在线配置API来减免大量的接口开发工作，可以在线配置图表实现数据可视化。


### 技术栈

lightning是由一系列的Django apps组件，前端是SPA，己打包到lightning app里面。

本项目上中使用了以下技术：

* [Django](https://www.djangoproject.com/)
* [React](https://reactjs.org/)
* [Ant Design](https://ant.design/)



<!-- GETTING STARTED -->
## 快速开始

在开始之前，需要先学习 [Python](https://www.python.org/) 与 [Django](https://www.djangoproject.com/)

### 准备

* **Python** 最低需要 3.6 版本
* **Django** 需要 2.2.x 版本，Django 3.x暂不支持。

### 安装

安装lightning 依赖

```sh
pip install django-lightning
```

### 配置

1. 在 [Django settings](https://docs.djangoproject.com/en/2.2/ref/settings/) 中导入`lightning.settings`下的配置

```python
from lightning.settings import *
```

2. 在 [Django settings](https://docs.djangoproject.com/en/2.2/ref/settings/) 的`INSTALLED_APPS`中添加`lightning.APPS`

```python
import lightning
INSTALLED_APPS += lightning.APPS
```

3. 配置根路由，在项目的urls.py中，把`lightning.urls`的路由添加到最后一行。
```python
from django.urls import path, include

urlpatterns = [
    # ...
    path('', include('lightning.urls')),  # 添加到最后一行
]
```

### Migrate

需要migrate一次，为lightning就用创建数据表。

```sh
./manage.py migrate
```

### 生成管理界面

使用`./manage.py light <app_label>` 生成指定应用的页面配置内容
```sh
./manage.py light my_app
```

### 运行

使用`./manage.py runserver` 运行Django项目
```sh
./manage.py runserver
```
此时，通过浏览器打开 http://localhost:8000/lightning 即可进入管理界面，使用管理员帐号登录即可。若未有帐号，使用`./manage.py createsuperuser` 命令创建一个。

## 了解更多

请查阅[参考文档](https://gitmen.gitee.io/lightning-doc/)以及[示例](https://gitmen.gitee.io/lightning-doc/docs/crm)

<!-- CONTRIBUTING -->
## 欢迎参与项目建设

我们本着回馈社区的初心把团队多年的积累开源，同时也希望社区中有志之士能参与到项目中一起完善她。你可以通过写代码的方式来参与，也可以通过测试提Bug、编写文档、文档国际化等形式参与进来。

<!-- LICENSE -->
## 授权协议

本开源项目基于MIT协议发布，更多信息请查看 `LICENSE` 。

<!-- CONTACT -->
## 联系人

Jeff Kit，项目负责人
- @jeff_kit(微信、推特)
- jeff@gitmen.com

