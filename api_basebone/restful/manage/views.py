from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import DatabaseError, transaction

from rest_framework import permissions, viewsets
from rest_framework.decorators import action

from api_basebone.app.account.forms import UserCreateUpdateForm

from api_basebone.core import admin, exceptions, const

from api_basebone.drf.response import success_response
from api_basebone.drf.pagination import PageNumberPagination

from api_basebone.restful.forms import get_form_class
from api_basebone.restful.manage import batch_actions
from api_basebone.restful.pip_flow import add_login_user_data
from api_basebone.restful.relations import (
    _create_update_pre_hand
)
from api_basebone.restful.serializers import (
    create_serializer_class,
    multiple_create_serializer_class
)

from api_basebone.utils import meta, get_app
from api_basebone.utils.operators import build_filter_conditions


class FormMixin(object):
    """表单处理集合"""

    def get_create_form(self):
        """获取创建数据的验证表单"""
        return get_form_class(self.model, 'create')

    def get_update_form(self):
        """获取更新数据的验证表单"""
        return get_form_class(self.model, 'update')

    def get_partial_update_form(self):
        return get_form_class(self.model, 'update')

    def get_validate_form(self, action):
        """获取验证表单"""
        return getattr(self, 'get_{}_form'.format(action))()

    def get_bsm_model_admin(self):
        """获取 BSM Admin 模块"""
        return meta.get_bsm_model_admin(self.model)


class QuerySetMixin:
    """结果集处理集合"""

    def get_queryset_by_filter_user(self, queryset):
        """通过用户过滤对应的数据集

        - 如果用户是超级用户，则不做任何过滤
        - 如果用户是普通用户，则客户端筛选的模型有引用到了用户模型，则过滤对应的数据集
        """
        user = self.request.user
        if user and user.is_staff and user.is_superuser:
            return queryset

        # 检测模型中是否有字段引用了用户模型
        has_user_field = meta.get_related_model_field(self.model, get_user_model())
        if has_user_field:
            # 如果有，则读取 BSM Admin 中的配置
            admin_class = self.get_bsm_model_admin()

            if admin_class:
                # 检测 admin 配置中是否指定了 auth_filter_field 属性
                try:
                    field_name = getattr(admin_class, admin.BSM_AUTH_FILTER_FIELD, None)
                    filter_by_login_user = getattr(admin_class, admin.BSM_FILTER_BY_LOGIN_USER, True)
                    if field_name:
                        return queryset.filter(**{field_name: user})
                except Exception:
                    pass
        return queryset

    def get_queryset_by_order_by(self, queryset):
        """结果集支持排序"""
        fields = self.request.data.get(const.ORDER_BY_FIELDS)
        if isinstance(fields, list) and fields:
            return queryset.order_by(*fields)
        return queryset

    def get_queryset_by_filter_conditions(self, queryset):
        """
        用于检测客户端传入的过滤条件

        客户端传入的过滤条件的数据结构如下：

        [
            {
                field: xxxx,
                operator: xxxx,
                value: xxxx
            }
        ]
        """
        if not queryset:
            return queryset

        filter_conditions = self.request.data.get(const.FILTER_CONDITIONS)
        if filter_conditions:
            cons = build_filter_conditions(filter_conditions)
            if cons:
                return queryset.filter(cons)
            return queryset
        return queryset

    def get_queryset_by_with_tree(self, queryset):
        """如果是树形结构，则需要做对应的过滤"""
        if self.tree_data:
            params = {
                self.tree_data[0]: self.tree_data[2]
            }
            return queryset.filter(**params)
        return queryset

    def _get_queryset(self, queryset):
        methods = ['filter_user', 'filter_conditions', 'order_by', 'with_tree']
        for item in methods:
            queryset = getattr(self, f'get_queryset_by_{item}')(queryset)
        return queryset


class GenericViewMixin:
    """重写 GenericAPIView 中的某些方法"""

    def perform_authentication(self, request):
        """
        截断，校验对应的 app 和 model 是否合法以及赋予当前对象对应的属性值

        - 检验 app 和 model 是否合法
        - 加载 admin 模块
        - 记录模型对象
        - 处理展开字段
        - 处理树形数据
        - 给数据自动插入用户数据
        """
        result = super().perform_authentication(request)
        self.app_label, self.model_slug = self.kwargs.get('app'), self.kwargs.get('model')

        # 检测应用是否在 INSTALLED_APPS 中
        if get_app(self.app_label) not in settings.INSTALLED_APPS:
            raise exceptions.BusinessException(error_code=exceptions.APP_LABEL_IS_INVALID)

        # 检测模型是否合法
        if self.model_slug not in apps.all_models[self.app_label]:
            raise exceptions.BusinessException(error_code=exceptions.MODEL_SLUG_IS_INVALID)

        self.model = apps.all_models[self.app_label][self.model_slug]

        meta.load_custom_admin_module()
        self.get_expand_fields()
        self._get_data_with_tree(request)

        add_login_user_data(self, request.data)
        return result

    def get_expand_fields(self):
        """获取扩展字段并作为属性值赋予

        注意使用扩展字段 get 方法和 post 方法的区别

        get 方法使用 query string，这里需要解析
        post 方法直接放到 body 中
        """
        self.expand_fields = None
        if self.action in ['list']:
            fields = self.request.query_params.get(const.EXPAND_FIELDS)
            self.expand_fields = fields.split(',') if fields else None
        elif self.action in ['retrieve', 'set']:
            self.expand_fields = self.request.data.get(const.EXPAND_FIELDS)
            # 详情的展开字段和列表的展开字段分开处理
            if not self.expand_fields and self.action == 'retrieve':
                # 对于详情的展开，直接读取 admin 中的配置
                admin_class = self.get_bsm_model_admin()
                if admin_class:
                    try:
                        detail_expand_fields = getattr(admin_class, admin.BSM_DETAIL_EXPAND_FIELDS, None)
                        if detail_expand_fields:
                            self.expand_fields = detail_expand_fields
                    except Exception:
                        pass

    def _get_data_with_tree(self, request):
        """检测是否可以设置树形结构"""
        self.tree_data = None

        data_with_tree = False
        # 检测客户端传进来的树形数据结构的参数
        if request.method.upper() == 'GET':
            data_with_tree = request.query_params.get(const.DATA_WITH_TREE, False)
        elif request.method.upper() == 'POST':
            data_with_tree = request.data.get(const.DATA_WITH_TREE, False)

        # 如果客户端传进来的参数为真，则通过 admin 配置校验，即 admin 中有没有配置
        if data_with_tree:
            admin_class = self.get_bsm_model_admin()
            if admin_class:
                try:
                    parent_field = getattr(admin_class, admin.BSM_PARENT_FIELD, None)
                    if parent_field:
                        # 获取父亲字段数据，包含字段名，related_name 和 默认值
                        # 这些数据在其他地方会用到
                        parent_field_data = meta.tree_parent_field(self.model, parent_field)
                        if parent_field_data:
                            self.tree_data = parent_field_data
                except Exception:
                    pass

    def translate_expand_fields(self, expand_fields):
        """转换展开字段"""
        for out_index, item in enumerate(expand_fields):
            field_list = item.split('.')
            model = self.model
            for index, value in enumerate(field_list):
                field = model._meta.get_field(value)
                if meta.check_field_is_reverse(field):
                    result = meta.get_relation_field_related_name(field.related_model, field.remote_field.name)
                    if result:
                        field_list[index] = result[0]
                if field.is_relation:
                    model = field.related_model
            expand_fields[out_index] = '.'.join(field_list)
        return expand_fields

    def get_queryset(self):
        """动态的计算结果集

        - 如果是展开字段，这里做好是否关联查询
        """
        expand_fields = self.expand_fields
        if not expand_fields:
            return self._get_queryset(self.model.objects.all())

        expand_fields = self.translate_expand_fields(expand_fields)
        field_list = [item.replace('.', '__') for item in expand_fields]
        return self._get_queryset(self.model.objects.all().prefetch_related(*field_list))

    def get_serializer_class(self, expand_fields=None):
        """动态的获取序列化类

        - 如果没有嵌套字段，则动态创建最简单的序列化类
        - 如果有嵌套字段，则动态创建引用字段的嵌套序列化类
        """
        # FIXME: 这里只有做是为了使用 django-rest-swagger，否则会报错，因为 swagger 还是很笨
        expand_fields = getattr(self, 'expand_fields', None)
        # FIXME: 这里设置了一个默认值，是为了避免 swagger 报错
        model = getattr(self, 'model', get_user_model())
        tree_data = getattr(self, 'tree_data', None)

        # 如果没有展开字段，则直接创建模型对应的序列化类
        if not expand_fields:
            return create_serializer_class(model, tree_structure=tree_data)

        # 如果有展开字段，则创建嵌套的序列化类
        serializer_class = multiple_create_serializer_class(
            model, expand_fields, tree_structure=tree_data
        )
        return serializer_class


class CommonManageViewSet(FormMixin,
                          QuerySetMixin,
                          GenericViewMixin,
                          viewsets.ModelViewSet):
    """通用的管理接口视图"""
    permission_classes = (permissions.IsAuthenticated, )
    pagination_class = PageNumberPagination

    def perform_create(self, serializer):
        return serializer.save()

    def perform_update(self, serializer):
        return serializer.save()

    def retrieve(self, request, *args, **kwargs):
        """获取数据详情"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(serializer.data)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            return success_response(response.data)

        serializer = self.get_serializer(queryset, many=True)
        return success_response(serializer.data)

    def _after_reverse_field_one_to_many(self, field, key, value, instance, detail=True):
        """处理反向字段的多对一的数据

        对于此种场景，数据格式是包含对象的列表或者已经存在对象的主键

        场景描述：
            class AModel(models.Model):
                pass

            class BModel(models.Model):
                a = models.ForgignKey(AModel)
                name = models.CharField()

        AModel 请求数据时，字段中包含 bmodel 对象如下数据格式：

            bmodel: [
                {
                    name: 'xxxx'
                }
            ]
            或者 
            bmodel: [
                {
                    'id': xxxx,
                    'name': 'update xxxxx'
                }
            ]
        """
        related_model = field.related_model
        pk_field_name = related_model._meta.pk.name

        if not isinstance(value, list):
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR,
                error_data=f'{key}: {value} 只能是列表'
            )

        # 这里需要判断创造和更新
        if detail:
            # 如果是更新，如果传入空的数据，则删除掉对应的数据
            if not value:
                try:
                    related_name = meta.get_relation_field_related_name(
                        field.related_model, field.remote_field.name
                    )
                    if related_name:
                        relation = getattr(instance, related_name[0], None)
                        if relation:
                            relation.all().delete()
                            return
                except Exception as e:
                    raise exceptions.BusinessException(
                        error_code=exceptions.PARAMETER_FORMAT_ERROR,
                        error_data=str(e)
                    )
        else:
            # 如果是创建，则什么都不做
            if not value:
                return

        pure_id_list, object_data_list = [], []
        for item in value:
            if isinstance(item, dict):
                object_data_list.append(item)
                pure_id_list.append(item.get(pk_field_name))
            else:
                pure_id_list.append(item)

        if object_data_list:
            for item in object_data_list:
                if not detail and pk_field_name in item:
                    raise exceptions.BusinessException(
                        error_code=exceptions.PARAMETER_BUSINESS_ERROR,
                        error_data=f'{key}: {value} 当前为 create 操作，不能传入包含主键的数据'
                    )

            for item_value in object_data_list:
                if pk_field_name in item_value:
                    # 此时说明是更新的数据
                    pk_value = related_model._meta.pk.to_python(item[pk_field_name])

                    filter_params = {
                        pk_field_name: pk_value,
                        field.remote_field.name: instance
                    }
                    obj = related_model.objects.filter(**filter_params).first()
                    if not obj:
                        raise exceptions.BusinessException(
                            error_code=exceptions.OBJECT_NOT_FOUND,
                            error_data=f'{key}: {value} 指定的主键找不到对应的数据'
                        )

                    serializer = create_serializer_class(related_model)(instance=obj, data=item_value, partial=True)
                    serializer.is_valid(raise_exception=True)
                    serializer.save()
                else:
                    # 如果传进来的数据不包含主键，则代表是创建数据
                    serializer = create_serializer_class(field.related_model)(data=item_value)
                    serializer.is_valid(raise_exception=True)
                    obj = serializer.save()
                    setattr(obj, field.remote_field.name, instance)
                    obj.save()
                    if detail:
                        pure_id_list.append(getattr(obj, pk_field_name))
        if detail and pure_id_list:
            pure_id_list = [related_model._meta.pk.to_python(item) for item in pure_id_list]
            related_model.objects.exclude(**{f'{pk_field_name}__in': pure_id_list}).delete()

    def _after_reverse_field_many_to_many(self, field, key, value, instance, detail=True):
        """处理反向字段的多对多数据

        场景类似上面杉树的注释
        """
        related_model = field.related_model
        pk_field_name = related_model._meta.pk.name

        if not (isinstance(value, list) and value):
            return

        pure_data, object_data, related_obj_set = [], [], set()
        for item in value:
            object_data.append(item) if isinstance(item, dict) else pure_data.append(item)

        if pure_data:
            queryset = related_model.objects.filter(
                **{f'{pk_field_name}__in': pure_data}
            )
            if len(pure_data) != queryset.count():
                raise exceptions.BusinessException(
                    error_code=exceptions.PARAMETER_BUSINESS_ERROR,
                    error_data=f'{key}: {value} 包含不合法的主键数据'
                )
            for item in queryset.iterator():
                related_obj_set.add(item.id)

        # 如果不包含对象数据，则不做任何处理
        if not object_data:
            create_list, update_list = [], []
            for item in object_data:
                update_list.append(item) if pk_field_name in item else create_list.append(item)

            if create_list:
                serializer = create_serializer_class(related_model)(data=create_list, many=True)
                serializer.is_valid(raise_exception=True)
                create_ids = [related_model.objects.create(**item).id for item in create_list]
                related_obj_set.update(create_ids)

            if update_list:
                update_data_map = {item[pk_field_name]: item for item in update_list}
                filter_params = {
                    f'{pk_field_name}__in': update_data_map.keys()
                }
                queryset = related_model.objects.filter(**filter_params)
                if queryset.count() != len(update_list):
                    raise exceptions.BusinessException(
                        error_code=exceptions.PARAMETER_FORMAT_ERROR,
                        error_data=f'{key}: {update_list} 存在不合法的数据'
                    )

                for instance in queryset.iterator():
                    data = update_data_map.get(getattr(instance, pk_field_name, None))
                    serializer = create_serializer_class(related_model)(instance=instance, data=data, partial=True)
                    serializer.is_valid(raise_exception=True)
                    serializer.save()
                related_obj_set.update(update_data_map.keys())
        related_name = meta.get_relation_field_related_name(related_model, field.remote_field.name)
        relation = getattr(instance, related_name, None)
        if relation:
            relation.set(list(related_obj_set))

    def _create_update_after_hand(self, request, instance, detail=True):
        """创建或者更新完毕后，处理反向字段的数据"""

        if not (request.data and isinstance(request.data, dict)):
            return

        for key, value in request.data.items():
            field = meta.get_relation_field(self.model, key, reverse=True)
            if not field:
                continue

            # 这里说明是反向字段
            if not field.concrete and field.remote_field:
                if field.many_to_many:
                    self._after_reverse_field_many_to_many(field, key, value, instance, detail=detail)
                else:
                    self._after_reverse_field_one_to_many(field, key, value, instance, detail=detail)

    def create(self, request, *args, **kwargs):
        """
        这里校验表单和序列化类分开创建

        原因：序列化类有可能嵌套
        """
        try:
            with transaction.atomic():
                try:
                    _create_update_pre_hand(self, request.data)

                    if self.model == get_user_model():
                        serializer = UserCreateUpdateForm(data=request.data)
                    else:
                        serializer = self.get_validate_form(self.action)(data=request.data)
                    serializer.is_valid(raise_exception=True)

                    instance = self.perform_create(serializer)

                    # 如果有联合查询，单个对象创建后并没有联合查询
                    instance = self.get_queryset().filter(id=instance.id).first()
                    serializer = self.get_serializer(instance)

                    self._create_update_after_hand(request, instance, detail=False)
                    return success_response(serializer.data)
                except exceptions.BusinessException as e:
                    message = e.error_data if e.error_data else e.error_message
                    raise DatabaseError(message)
                except Exception as e:
                    raise DatabaseError(str(e))
        except DatabaseError as e:
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_BUSINESS_ERROR,
                error_data=str(e)
            )

    def update(self, request, *args, **kwargs):
        """全量更新数据"""
        try:
            with transaction.atomic():
                try:
                    _create_update_pre_hand(self, request.data)

                    partial = kwargs.pop('partial', False)
                    instance = self.get_object()

                    if self.model == get_user_model():
                        serializer = UserCreateUpdateForm(instance, data=request.data, partial=partial)
                    else:
                        serializer = self.get_validate_form(self.action)(instance, data=request.data, partial=partial)
                    serializer.is_valid(raise_exception=True)

                    instance = self.perform_update(serializer)
                    serializer = self.get_serializer(instance)

                    if getattr(instance, '_prefetched_objects_cache', None):
                        instance._prefetched_objects_cache = {}

                    self._create_update_after_hand(request, instance)
                    return success_response(serializer.data)
                except exceptions.BusinessException as e:
                    message = e.error_data if e.error_data else e.error_message
                    raise DatabaseError(message)
                except Exception as e:
                    raise DatabaseError(str(e))
        except DatabaseError as e:
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_BUSINESS_ERROR,
                error_data=str(e)
            )

    def partial_update(self, request, *args, **kwargs):
        """部分字段更新"""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """删除数据"""
        instance = self.get_object()
        self.perform_destroy(instance)
        return success_response()

    @action(methods=['POST'], detail=False, url_path='list')
    def set(self, request, app, model, **kwargs):
        """获取列表数据"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            return success_response(response.data)

        serializer = self.get_serializer(queryset, many=True)
        return success_response(serializer.data)

    @action(methods=['POST'], detail=False, url_path='batch')
    def batch(self, request, app, model, **kwargs):
        """
        ## 批量操作

        ```python
        {
            action: 动作,
            data: 主键的列表
        }
        ```
        """
        serializer = batch_actions.BatchActionForm(
            data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        serializer.handle()
        return success_response()
