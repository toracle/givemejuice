# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function, unicode_literals)

from bothub_client.bot import BaseBot
from bothub_client.messages import Message


class Bot(BaseBot):
    """Represent a Bot logic which interacts with a user.

    BaseBot superclass have methods belows:

    * Send message
      * self.send_message(message, chat_id=None, channel=None)
    * Data Storage
      * self.set_project_data(data)
      * self.get_project_data()
      * self.set_user_data(data, user_id=None, channel=None)
      * self.get_user_data(user_id=None, channel=None)

    When you omit user_id and channel argument, it regarded as a user
    who triggered a bot.
    """

    def handle_message(self, event, context):
        """Handle a message received

        event is a dict and contains trigger info.

        {
           "trigger": "webhook",
           "channel": "<name>",
           "sender": {
              "id": "<chat_id>",
              "name": "<nickname>"
           },
           "content": "<message content>",
           "raw_data": <unmodified data itself webhook received>
        }
        """
        content = event.get('content')

        if not content:
            if event['new_joined']:
                self.send_chatroom_welcome_message(event)
            return

        if content == '/start':
            self.send_welcome_message(event)
        elif content == '메뉴보기':
            self.send_menu(event)
        # be aware of tailing space
        elif content.startswith('/show '):
            self.send_show(content, event)
        # be aware of tailing space
        elif content.startswith('/order_confirm '):
            self.send_order_confirm(content, event)
        elif content.startswith('/order '):
            self.send_order(content, event)
        elif content.startswith('/done '):
            self.send_drink_done(content, event)
        elif content == '/feedback':
            self.send_feedback_request()
        else:
            data = self.get_user_data()
            wait_feedback = data.get('wait_feedback')
            if wait_feedback:
                self.send_feedback(content, event)

    def send_welcome_message(self, event):
        message = Message(event).set_text('반가워요, GiveMeJuice입니다.\n'\
                                          '무더운 여름철, 건강하고 시원한 주스 한 잔 어떠세요?')\
                                .add_quick_reply('메뉴보기')
        self.send_message(message)

    def send_menu(self, event):
        menu = self.get_project_data()['menu']
        names = [name for name in menu.keys()]
        message = Message(event).set_text('어떤 음료를 원하세요?')

        for name in names:
            message.add_postback_button(name, '/show {}'.format(name))

        self.send_message(message)

    def send_show(self, content, event):
        menu = self.get_project_data()['menu']
        _, name = content.split()
        selected_menu = menu[name]
        text = '{name}는 {description}\n가격은 {price}원이예요.'.format(name=name, **selected_menu)
        message = Message(event).set_text(text)\
                                .add_quick_reply('{} 주문'.format(name), '/order_confirm {}'.format(name))\
                                .add_quick_reply('메뉴보기')

        self.send_message(message)

    def send_order_confirm(self, content, event):
        _, name = content.split()
        message = Message(event).set_text('{}를 주문하시겠어요?'.format(name))\
                                .add_quick_reply('예', '/order {}'.format(name))\
                                .add_quick_reply('취소', '메뉴보기')
        self.send_message(message)

    def send_order(self, content, event):
        _, name = content.split()
        self.send_message('{}를 주문했습니다. 음료가 준비되면 알려드릴께요.'.format(name))

        chat_id = self.get_project_data().get('chat_id')
        order_message = Message(event).set_text('{} 1잔 주문 들어왔습니다!'.format(name))\
                                      .add_quick_reply('완료', '/done {} {}'.format(event['sender']['id'], name))

        self.send_message(order_message, chat_id=chat_id)

    def send_chatroom_welcome_message(self, event):
        self.remember_chatroom(event)
        message = Message(event).set_text('안녕하세요? GiveMeJuice 봇입니다.\n'\
                                          '저는 여러분들을 도와 고객들의 음료 주문을 받고, 고객의 의견을 여러분께 전달해드립니다.')
        self.send_message(message)

    def remember_chatroom(self, event):
        chat_id = event.get('chat_id')
        data = self.get_project_data()
        data['chat_id'] = chat_id
        self.set_project_data(data)

    def send_drink_done(self, content, event):
        _, sender_id, menu_name = content.split()
        self.send_message('{}가 준비되었습니다. 카운터에서 수령해주세요.'.format(menu_name), chat_id=sender_id)
        message = Message(event).set_text('저희 가게를 이용하신 경험을 말씀해주시면 많은 도움이 됩니다.')\
                                .add_quick_reply('평가하기', '/feedback')
        self.send_message(message, chat_id=sender_id)
        self.send_message('고객분께 음료 완료 알림을 전송했습니다.')

    def send_feedback_request(self):
        self.send_message('음료는 맛있게 즐기셨나요? 어떤 경험을 하셨는지 알려주세요. 격려나 제안 모두 큰 도움이 됩니다.')
        data = self.get_user_data()
        data['wait_feedback'] = True
        self.set_user_data(data)

    def send_feedback(self, content, event):
        chat_id = self.get_project_data().get('chat_id')
        self.send_message('고객의 평가 메세지입니다:\n{}'.format(content), chat_id=chat_id)

        message = Message(event).set_text('평가해주셔서 감사합니다!')\
                                .add_quick_reply('메뉴보기')
        self.send_message(message)
        data = self.get_user_data()
        data['wait_feedback'] = False
        self.set_user_data(data)
