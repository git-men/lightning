import requests
import logging
from copy import copy

from django.db import transaction
from django.db.models.query import QuerySet
from django.apps import apps
from django.http import HttpResponse
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from api_basebone.permissions import BasePermission
from api_basebone.core import exceptions
from api_basebone.settings import settings
from api_basebone.signals import post_bsm_create, post_bsm_delete, before_bsm_create, before_bsm_delete
from api_basebone.restful.funcs import find_func, get_funcs
from api_basebone.restful.relations import forward_relation_hand, reverse_relation_hand
from api_basebone.drf.response import success_response, get_or_create_logger
from api_basebone.sandbox.logger import LogCollector
from api_basebone.restful.client import user_pip as client_user_pip

log = logging.getLogger(__name__)


def filter_display_fields(data, display_fields):
    """从json数据中筛选，只保留显示的列"""
    if not display_fields:
        """没有限制的情况下，显示所有"""
        return data

    display_fields_set = set()
    for field_str in display_fields:
        if field_str.startswith('-'):
            display_fields_set.add(field_str)
        else:
            items = field_str.split('.')
            for i in range(len(items)):
                display_fields_set.add('.'.join(items[: i + 1]))
    if isinstance(data, list):
        results = []
        for record in data:
            display_record = filter_sub_display_fields(display_fields_set, record)
            results.append(display_record)
        return results
    elif isinstance(data, dict):
        return filter_sub_display_fields(display_fields_set, data)


def filter_sub_display_fields(display_fields_set, record, prefix=''):
    display_record = {}

    # 星号为通配符，该层所有属性都匹配
    if prefix:
        star_key = prefix + '.*'
    else:
        star_key = '*'

    for k, v in record.items():
        if prefix:
            full_key = prefix + '.' + k
        else:
            full_key = k
        exclude_key = '-' + full_key

        # 负号优先级高于星号
        if exclude_key in display_fields_set:
            """负号表示该属性不显示"""
            continue

        if isinstance(v, list):
            if (star_key not in display_fields_set) and (
                full_key not in display_fields_set
            ):
                """星号为通配符"""
                continue

            display_record[k] = []
            for d in v:
                if isinstance(d, dict):
                    sub_record = filter_sub_display_fields(
                        display_fields_set, d, full_key
                    )
                    display_record[k].append(sub_record)
                else:
                    display_record[k].append(d)
        elif isinstance(v, dict):
            if (star_key not in display_fields_set) and (
                full_key not in display_fields_set
            ):
                """星号为通配符"""
                continue
            display_record[k] = filter_sub_display_fields(display_fields_set, v, full_key)
        # 星号优先级高于具体的列名
        elif star_key in display_fields_set:
            """星号为通配符"""
            display_record[k] = v
        elif full_key in display_fields_set:
            display_record[k] = v
    return display_record


def display(genericAPIView, display_fields):
    """查询操作，取名display，避免跟列表list冲突"""
    queryset = genericAPIView.filter_queryset(genericAPIView.get_queryset())

    page = genericAPIView.paginate_queryset(queryset)
    if page is not None:
        """分页查询"""
        serializer = genericAPIView.get_serializer(page, many=True)
        result = filter_display_fields(serializer.data, display_fields)
        response = genericAPIView.get_paginated_response(result)
        result = response.data
    else:
        serializer = genericAPIView.get_serializer(queryset, many=True)
        result = filter_display_fields(serializer.data, display_fields)
    return success_response(result)


def retrieve(genericAPIView, display_fields):
    """获取数据详情"""
    instance = genericAPIView.get_object()
    serializer = genericAPIView.get_serializer(instance)
    result = filter_display_fields(serializer.data, display_fields)
    return success_response(result)


def client_func(genericAPIView, user, app, model, func_name, params):
    """云函数, 由客户端直接调用的服务函数
        """
    func, options = find_func(app, model, func_name)
    if not func:
        raise exceptions.BusinessException(
            error_code=exceptions.FUNCTION_NOT_FOUNT,
            error_data=f'no such func: {func_name} found',
        )

    if options.get('login_required', False):
        if not user.is_authenticated:
            raise PermissionDenied()

    view_context = {'view': genericAPIView}
    params['view_context'] = view_context

    result = func(user, **params)
    # TODO：考虑函数的返回结果类型。1. 实体，2.实体列表，3.字典，4.无返回，针对不同的结果给客户端反馈
    if isinstance(result, requests.Response):
        return HttpResponse(result, result.headers.get('Content-Type', None))
    if isinstance(result, (list, dict)):
        return success_response(result)
    if isinstance(result, genericAPIView.model):
        serializer = genericAPIView.get_serializer(result)
        return success_response(serializer.data)
    return success_response()

def functions(genericAPIView, app, model, scene):
    """获取云函数的定义，分别从代码和数据库中获取。
    """
    funcs = get_funcs(app, model, scene)
    return success_response(funcs)


def manage_func(genericAPIView, user, app, model, func_name, params):
    """云函数, 由客户端直接调用的服务函数
        """
    # import ipdb; ipdb.set_trace()
    func, options = find_func(app, model, func_name)
    if not func:
        raise exceptions.BusinessException(
            error_code=exceptions.FUNCTION_NOT_FOUNT,
            error_data=f'no such func: {func_name} found',
        )
    if options.get('login_required', False):
        if not user.is_authenticated:
            raise PermissionDenied()
    if options.get('staff_required', False):
        if not user.is_staff:
            raise PermissionDenied()
    if options.get('superuser_required', False):
        if not user.is_superuser:
            raise PermissionDenied()
    if options.get('permissions', []):
        permissions = options['permissions']
        literal_pers = [per.strip() for per in permissions if isinstance(per, str) and per.strip() != '']
        cls_pers = [per for per in permissions if isinstance(per, type) and issubclass(per, BasePermission)]

        if literal_pers:
            content_type = ContentType.objects.get(app_label=app, model=model)
            per_names = [per[0] for per in Permission.objects.filter(codename__in=literal_pers, content_type=content_type).values_list('codename')]
            if set(literal_pers) != set(per_names):
                raise PermissionDenied()
        
        for cls_per in cls_pers:
            if not cls_per().has_permission(user, apps.get_model(app, model), func_name, params, genericAPIView.request):
                raise PermissionDenied()

    view_context = {
        'view': genericAPIView
    }
    params['view_context'] = view_context
    params.update({
        'request': genericAPIView.request,
        'current_model': f'{app}__{model}',
        'current_model_cls': apps.get_model(app, model),
        'logger': get_or_create_logger(func_name, 'function')
    })
    

    if options.get('atomic', True):
        with transaction.atomic():
            result = func(user, **params)
    else:
        result = func(user, **params)

    if isinstance(result, requests.Response):
        response = HttpResponse(result, result.headers.get('Content-Type', None))
        if 'Content-disposition' in result.headers:
            response['Content-disposition'] = result.headers.get('Content-disposition')
        return response
    if isinstance(result, genericAPIView.model):
        serializer = genericAPIView.get_serializer(result)
        return success_response(serializer.data)
    if isinstance(result, QuerySet):
        serializer = genericAPIView.get_serializer(result, many=True)
        return success_response(serializer.data)
    if isinstance(result, HttpResponse) or isinstance(result, Response):
        return result
    rsp = success_response()
    try:
        rsp = success_response(result)
    except:
        pass
    return rsp


def client_create(genericAPIView, request, set_data):
    """
        这里校验表单和序列化类分开创建

        原因：序列化类有可能嵌套
        """

    with transaction.atomic():
        client_user_pip.add_login_user_data(genericAPIView, set_data)
        forward_relation_hand(genericAPIView.model, set_data)
        serializer = genericAPIView.get_validate_form(genericAPIView.action)(
            data=set_data
        )
        serializer.is_valid(raise_exception=True)

        before_bsm_create.send(
            sender=genericAPIView.model,
            instance=serializer.validated_data,
            create=True,
            request=genericAPIView.request
        )
        instance = genericAPIView.perform_create(serializer)
        reverse_relation_hand(genericAPIView.model, set_data, instance, detail=False)
        instance = genericAPIView.get_queryset().get(pk=instance.pk)

        # with transaction.atomic():
        log.debug(
            'sending Post Save signal with: model: %s, instance: %s',
            genericAPIView.model,
            instance,
        )
        post_bsm_create.send(
            sender=genericAPIView.model,
            instance=instance,
            create=True,
            request=genericAPIView.request,
            old_instance=None,
            scope='client',
        )
        # 如果有联合查询，单个对象创建后并没有联合查询, 所以要多查一次？
        serializer = genericAPIView.get_serializer(
            genericAPIView.get_queryset().get(pk=instance.pk)
        )
        return success_response(serializer.data)


def manage_create(genericAPIView, request, set_data):
    """
        这里校验表单和序列化类分开创建

        原因：序列化类有可能嵌套
        """
    many = isinstance(set_data, list)
    with transaction.atomic():
        forward_relation_hand(genericAPIView.model, set_data)
        serializer = genericAPIView.get_validate_form(genericAPIView.action)(
            data=set_data, context=genericAPIView.get_serializer_context(),
            many=many
        )
        serializer.is_valid(raise_exception=True)
        before_bsm_create.send(
            sender=genericAPIView.model,
            instance=serializer.validated_data,
            create=True,
            request=genericAPIView.request,
            scope='admin'
        )
        instance = genericAPIView.perform_create(serializer)

        if many:
            # 如果是批量插入，则直接返回
            return success_response()

        # 如果有联合查询，单个对象创建后并没有联合查询
        instance = genericAPIView.get_queryset().filter(pk=instance.pk).first()
        serializer = genericAPIView.get_serializer(instance)
        reverse_relation_hand(genericAPIView.model, set_data, instance, detail=False)

        log.debug(
            'sending Post Save signal with: model: %s, instance: %s',
            genericAPIView.model,
            instance,
        )
        post_bsm_create.send(
            sender=genericAPIView.model,
            instance=instance,
            create=True,
            request=genericAPIView.request,
            old_instance=None,
            scope='admin'
        )
    return success_response(serializer.data)


def client_update(genericAPIView, request, partial, set_data):
    """全量更新数据"""
    with transaction.atomic():
        client_user_pip.add_login_user_data(genericAPIView, set_data)
        forward_relation_hand(genericAPIView.model, set_data)

        # partial = kwargs.pop('partial', False)
        instance = genericAPIView.get_object()
        old_instance = copy(instance)

        serializer = genericAPIView.get_validate_form(genericAPIView.action)(
            instance, data=set_data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        instance_dict = {'id': instance.pk}
        instance_dict.update(serializer.validated_data)
        before_bsm_create.send(
            sender=genericAPIView.model,
            instance=instance_dict,
            create=False,
            request=genericAPIView.request
        )
        instance = genericAPIView.perform_update(serializer)

        reverse_relation_hand(genericAPIView.model, set_data, instance)
        instance = genericAPIView.get_queryset().get(pk=instance.pk)

        # with transaction.atomic():
        log.debug(
            'sending Post Update signal with: model: %s, instance: %s',
            genericAPIView.model,
            instance,
        )
        post_bsm_create.send(
            sender=genericAPIView.model,
            instance=instance,
            create=False,
            request=genericAPIView.request,
            old_instance=old_instance,
            scope='client'
        )

        serializer = genericAPIView.get_serializer(
            genericAPIView.get_queryset().get(pk=instance.pk)
        )
        return success_response(serializer.data)


def manage_update(genericAPIView, request, partial, set_data):
    """全量更新数据"""
    print('进入全量更新了吗？')
    with transaction.atomic():
        forward_relation_hand(genericAPIView.model, set_data)

        # partial = kwargs.pop('partial', False)
        instance = genericAPIView.get_object()
        old_instance = copy(instance)
        serializer = genericAPIView.get_validate_form(genericAPIView.action)(
            instance,
            data=set_data,
            partial=partial,
            context=genericAPIView.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        instance_dict = {'id': instance.pk}
        instance_dict.update(serializer.validated_data)
        before_bsm_create.send(
            sender=genericAPIView.model,
            instance=instance_dict,
            create=False,
            request=genericAPIView.request,
            scope='admin'
        )
        instance = genericAPIView.perform_update(serializer)
        serializer = genericAPIView.get_serializer(instance)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        reverse_relation_hand(genericAPIView.model, set_data, instance)

    # with transaction.atomic():  # 与主流程同一个事务
        log.debug(
            'sending Post Update signal with: model: %s, instance: %s',
            genericAPIView.model,
            instance,
        )
        post_bsm_create.send(
            sender=genericAPIView.model,
            instance=instance,
            create=False,
            old_instance=old_instance,
            request=genericAPIView.request,
            scope='admin'
        )
    return success_response(serializer.data)


def update_sort(genericAPIView, request, data):
    if data.get('dragId') == data.get('hoverId'):
        return
    instance = genericAPIView.model
    admin = genericAPIView.get_bsm_model_admin()
    sort_key = admin.sort_key
    from django.db.models import F, Q

    with transaction.atomic():
        dragItem = instance.objects.filter(id=data['dragId']).first()
        hoverItem = instance.objects.filter(id=data['hoverId']).first()
        dragIndex = getattr(dragItem, sort_key)
        hoveIndex = getattr(hoverItem, sort_key)
        isDownward = dragIndex < hoveIndex or (
            dragIndex == hoveIndex and dragItem.id < hoverItem.id
        )
        instance.objects.filter(id=data['dragId']).update(
            **{'parent': hoverItem.parent, sort_key: hoveIndex + 1}
        )

        instance.objects.filter(
            Q(parent=hoverItem.parent),
            ~Q(id=dragItem.id),
            Q(**{f'{sort_key}__gt': hoveIndex}),
        ).update(**{f'{sort_key}': F(f'{sort_key}') + 2})
        up = Q(id__gt=hoverItem.id) if isDownward else Q(id__gte=hoverItem.id)
        instance.objects.filter(
            Q(parent=hoverItem.parent),
            ~Q(id=dragItem.id),
            Q(**{f'{sort_key}': hoveIndex}),
            up,
        ).update(**{f'{sort_key}': F(f'{sort_key}') + 2})
    return success_response(instance.objects.all().values())


def destroy(genericAPIView, request, scope=''):
    """删除数据"""
    with transaction.atomic():
        instance = genericAPIView.get_object()
        old_instance = copy(instance)
        before_bsm_delete.send(
            sender=genericAPIView.model, instance=old_instance, request=genericAPIView.request, scope=scope
        )
        genericAPIView.perform_destroy(instance)
        post_bsm_delete.send(
            sender=genericAPIView.model, instance=old_instance, request=genericAPIView.request, scope=scope
        )
    return success_response()


def delete_by_conditon(genericAPIView):
    """按查询条件删除"""
    queryset = genericAPIView.filter_queryset(genericAPIView.get_queryset())
    deleted, rows_count = queryset.delete()
    result = {'deleted': deleted}

    return success_response(result)


def update_by_conditon(genericAPIView, set_fields):
    queryset = genericAPIView.filter_queryset(genericAPIView.get_queryset())
    count = queryset.update(**set_fields)
    result = {'count': count}
    return success_response(result)

