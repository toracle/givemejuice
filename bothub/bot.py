# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function, unicode_literals)

from bothub_client.bot import BaseBot
from bothub_client.messages import Message
from bothub_client.decorators import command


class Bot(BaseBot):
    @command('start')
    def send_welcome_message(self, event, context, args):
        '''/start 명령이 들어온 경우 안내 메세지를 출력한다.'''
        # 메세지를 생성한다
        message = Message(event).set_text('반가워요, GiveMeJuice입니다.\n'\
                                          '무더운 여름철, 건강하고 시원한 주스 한 잔 어떠세요?')\
                                .add_quick_reply('메뉴보기', '/menu')
        # 메세지를 전송한다
        self.send_message(message)

    @command('menu')
    def send_menu(self, event, context, args):
        '''/menu 명령이 들어왔을 때, 메뉴를 안내한다. 각 메뉴 항목은 postback 버튼으로 구성한다.'''
        # 프로젝트 저장소로부터 메뉴를 불러온다
        menu = self.get_project_data()['menu']

        # 메뉴 이름 목록을 생성한다
        names = [name for name in menu.keys()]

        # 메세지를 생성한다
        message = Message(event).set_text('어떤 음료를 원하세요?')

        # 각 메뉴 이름을 돌면서
        for name in names:
            # 메세지에 메뉴 설명 버튼을 추가한다
            message.add_postback_button(name, '/show {}'.format(name))

        # 메세지를 보낸다
        self.send_message(message)

    @command('show')
    def send_show(self, event, context, args):
        '''/show 명령이 이름 인자와 함께 들어왔을 때, 특정 메뉴의 설명과 가격을 안내한다.'''
        # 인자 목록으로부터 이름을 가져온다
        name = args[0]

        # 프로젝트 저장소로부터 메뉴를 불러온다
        menu = self.get_project_data()['menu']

        # 선택된 메뉴 항목을 가져온다
        selected_menu = menu[name]

        # 메세지 문자열을 만든다
        text = '{name}는 {description}\n가격은 {price}원이예요.'.format(name=name, **selected_menu)

        # 메세지에 문자열과 버튼을 붙인다
        message = Message(event).set_text(text)\
                                .add_quick_reply('{} 주문'.format(name), '/order {}'.format(name))\
                                .add_quick_reply('메뉴보기', '/menu')

        # 메세지를 보낸다
        self.send_message(message)

    @command('order_confirm')
    def send_order_confirm(self, event, context, args):
        '''/order_confirm 명령이 이름 인자와 함께 들어왔을 때, 주문 확인 메세지와 주문 버튼을 안내한다.'''
        # 인자 목록으로부터 이름을 가져온다
        name = args[0]

        # 주문 확인 메세지와 주문 버튼을 생성한다
        message = Message(event).set_text('{}를 주문하시겠어요?'.format(name))\
                                .add_quick_reply('예', '/order {}'.format(name))\
                                .add_quick_reply('취소', '/menu')

        # 메세지를 보낸다
        self.send_message(message)

    def on_default(self, event, context):
        '''dispatcher에 의해 처리되지 않은, 다른 메세지들을 처리할 기본 handler'''

        # 메세지 문자열을 가져온다
        content = event.get('content')

        # 메세지가 없다면
        if not content:
            # 봇이 들어있는 단체방에 누군가 들어온다면 new_joined에 값이 참으로 들어온다.
            # 만약 event에 new_joined 값이 있으며, 그 값이 참이면,
            if 'new_joined' in event and event['new_joined']:
                # 메세지를 보낸다
                self.send_chatroom_welcome_message(event)
            # 함수를 종료한다
            return

        # 사용자 저장소를 가져온다
        data = self.get_user_data()

        # 피드백 대기중인지 여부를 가져온다
        wait_feedback = data.get('wait_feedback')

        # 만약 피드백 대기중이라면
        if wait_feedback:
            # 작성된 피드백을 단체방에 보낸다
            self.send_feedback(content, event)
            return

        # try to recognize the statement
        recognized = self.recognize(event, context)
        if recognized:
            return
        self.send_error_message(event)

    def send_chatroom_welcome_message(self, event):
        '''단체방 환영 메세지를 보낸다'''
        # 이 대화방의 ID를 기억한다
        self.remember_chatroom(event)

        # 메세지를 생성한다
        message = Message(event).set_text('안녕하세요? GiveMeJuice 봇입니다.\n'\
                                          '저는 여러분들을 도와 고객들의 음료 주문을 받고, 고객의 의견을 여러분께 전달해드립니다.')

        # 메세지를 보낸다
        self.send_message(message)

    def remember_chatroom(self, event):
        '''대화방의 ID를 기억한다'''
        # event로부터 이 대화방의 ID를 가져온다
        chat_id = event.get('chat_id')

        # 프로젝트 저장소로부터 값을 가져온다
        data = self.get_project_data()

        # 프로젝트 저장소의 값에 대화방 ID를 추가한다
        data['chat_id'] = chat_id

        # 프로젝트 저장소에 값을 저장한다
        self.set_project_data(data)

    @command('order')
    def send_order(self, event, context, args):
        '''/order 명령이 이름 인자와 함께 들어왔을 때, 해당 메뉴가 주문되었음을 알리는 메세지를 보내고 단체방에 알린다'''
        # 인자 목록으로부터 이름을 가져온다
        name = args[0]

        quantity = args[1] if len(args) > 1 else 1

        # 메세지를 고객에게 보낸다
        self.send_message('{}를 {}잔 주문했습니다. 음료가 준비되면 알려드릴께요.'.format(name, quantity))

        # 단체방의 ID를 프로젝트 저장소에서 가져온다.
        chat_id = self.get_project_data().get('chat_id')

        # 주문되었음을 알리는 메세지를 생성한다
        order_message = Message(event).set_text('{} {}잔 주문 들어왔습니다!'.format(name, quantity))\
                                      .add_quick_reply('완료', '/done {} {}'.format(event['sender']['id'], name))

        # 메세지를 단체방에 보낸다
        self.send_message(order_message, chat_id=chat_id)

    @command('done')
    def send_drink_done(self, event, context, args):
        '''/done 명령이 들어왔을 때, 주문이 완료되었음을 고객에게 알린다'''
        # 이벤트로부터 메세지 문자열을 가져온다
        content = event.get('content')

        # 메세지 문자열을 공백으로 잘라서, 주문한 사람과 주문 품목을 가져온다
        _, sender_id, menu_name = content.split()

        # 고객에게 주문 완료 메세지를 보낸다
        self.send_message('{}가 준비되었습니다. 카운터에서 수령해주세요.'.format(menu_name), chat_id=sender_id)

        # 고객에게 평가를 요청하는 메세지를 보낸다
        message = Message(event).set_text('저희 가게를 이용하신 경험을 말씀해주시면 많은 도움이 됩니다.')\
                                .add_quick_reply('평가하기', '/feedback')
        self.send_message(message, chat_id=sender_id)

        message = Message(event).set_text('고객분께 음료 완료 알림을 전송했습니다.')
        # 단체방에 메세지를 보낸다
        self.send_message(message)

    @command('feedback')
    def send_feedback_request(self, event, context, args):
        '''/feedback 명령이 들어왔을 때, 피드백 요청 메세지를 보낸다'''
        # 피드백 요청 메세지를 보낸다
        self.send_message('음료는 맛있게 즐기셨나요? 어떤 경험을 하셨는지 알려주세요. 격려, 꾸지람 모두 큰 도움이 됩니다.')
        data = self.get_user_data()
        data['wait_feedback'] = True
        self.set_user_data(data)

    def send_feedback(self, content, event):
        chat_id = self.get_project_data().get('chat_id')
        self.send_message('고객의 평가 메세지입니다:\n{}'.format(content), chat_id=chat_id)

        message = Message(event).set_text('평가해주셔서 감사합니다!')\
                                .add_quick_reply('메뉴보기', '/menu')
        self.send_message(message)
        data = self.get_user_data()
        data['wait_feedback'] = False
        self.set_user_data(data)

    def recognize(self, event, context):
        response = self.nlu('apiai').ask(event=event)
        action = response.action

        message = Message(event)

        if action.intent == 'input.unknown':
            return False

        if not action.completed:
            message.set_text(response.next_message)
            self.send_message(message)
            return True

        if action.intent == 'show-menu':
            self.send_menu(event, context, [])
            return True

        if action.intent == 'order-drink':
            params = action.parameters
            self.send_order(event, context, (params['menu'], params['quantity']))
            return True

        message.set_text(response.next_message)
        self.send_message(message)
        return True

    def send_error_message(self, event):
        message = Message(event).set_text('잘 못알아들었어요.\n'\
                                          '무더운 여름철, 건강하고 시원한 주스 한 잔 어떠세요?')\
                                .add_quick_reply('메뉴보기', '/menu')
        self.send_message(message)
