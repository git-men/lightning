from __future__ import absolute_import, unicode_literals

from wechatpy.client.api.base import BaseWeChatAPI


class WeChatLogistics(BaseWeChatAPI):
    def add_order(self, add_source, wx_appid, order_id, openid,delivery_id, biz_id, 
    custom_remark, sender, receiver, cargo, shop, insured, service, expect_time=0, tagid=None):
        """
        添加运单
        详情请参考
        https://developers.weixin.qq.com/miniprogram/dev/api-backend/open-api/express/by-business/logistics.addOrder.html
        """

        data={
                'add_source': add_source, 
                'wx_appid': wx_appid, 
                'order_id': order_id, 
                'openid': openid,
                'delivery_id': delivery_id, 
                'biz_id': biz_id, 
                'custom_remark': custom_remark, 
                'sender': sender, 
                'receiver': receiver, 
                'cargo': cargo, 
                'shop': shop, 
                'insured': insured, 
                'service': service, 
                'expect_time': expect_time,
                'tagid': tagid, 
            }

        print('-------------------------------data----------------------------')
        print(data)

        return self._post(
            'express/business/order/add',
            data = data
        )
    
    def cancel_order(self, order_id, delivery_id, waybill_id, openid=None):
        """
        取消运单
        """

        return self._post(
            'express/business/order/cancel',
            data = {
                'order_id': order_id, 
                'openid': openid, 
                'delivery_id': delivery_id,
                'waybill_id': waybill_id
            }
        )
    
    def get_order(self, order_id,delivery_id, waybill_id, openid=None):
        """
        获取运单数据
        """

        return self._post(
            'express/business/order/get',
            data = {
                'order_id': order_id,
                'openid': openid,
                'delivery_id': delivery_id,
                'waybill_id': waybill_id
            }
        )

    def get_path(self, order_id, delivery_id, waybill_id, openid=None):
        """
        获取运单轨迹
        """

        return self._post(
            'express/business/path/get',
            data = {
                'order_id': order_id,	
                'openid': openid,	
                'delivery_id': delivery_id,
                'waybill_id': waybill_id,
            }
        )

    def get_quota(self, delivery_id, biz_id):
        """
        获取电子面单余额。仅在使用加盟类快递公司时，才可以调用。
        """
        
        return self._post(
            'express/business/quota/get',
            data = {
                delivery_id, 
                biz_id
            }
        )

    def test_update_order(self,biz_id, order_id, delivery_id, waybill_id, action_time, action_type, action_msg):
        # biz_id	string		是	商户id,需填test_biz_id
        # order_id	string		是	订单号
        # delivery_id	string		是	快递公司id,需填TEST
        # waybill_id	string		是	运单号
        # action_time	number		是	轨迹变化 Unix 时间戳
        # action_type	number		是	轨迹变化类型
        # action_msg

        data = {
            'biz_id': biz_id, 
            'order_id': order_id, 
            'delivery_id': delivery_id, 
            'waybill_id': waybill_id, 
            'action_time': action_time, 
            'action_type': action_type, 
            'action_msg': action_msg
        }
        print(data)

        return self._post(
            'express/business/test_update_order',
            data = data
        )