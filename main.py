from random import randrange
import re
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_user import get_user_info, get_city_id
import sqlalchemy
from sqlalchemy import and_
from sqlalchemy.orm import sessionmaker
from schema import create_tables, User, BlackList, Favorite


class Connect:
    def __init__(self, engine):
        self.engine = engine
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()


def write_msg(vk, user_id, message, buttons, attachment=''):
    if attachment == '':
        vk.method('messages.send',
                  {'user_id': user_id,
                   'message': message,
                   'random_id': randrange(10 ** 7),
                   'keyboard': buttons})
    else:
        vk.method('messages.send',
                  {'user_id': user_id,
                   'message': message,
                   'attachment': attachment,
                   'random_id': randrange(10 ** 7),
                   'keyboard': buttons
                   })


def write_simple_msg(vk, user_id, message):
    vk.method('messages.send',
              {'user_id': user_id,
               'message': message,
               'random_id': randrange(10 ** 7)
               })


def create_message_for_candidate(first_name, last_name, url_profile):
    result = f'Имя: {first_name}\n' \
             f'Фамилия: {last_name}\n' \
             f'Ссылка: {url_profile}\n'
    return result


def run_bot(access_token, DB_PORT, DB_NAME, DB_HOST,
            DB_ENGINE, DB_USERNAME, DB_PASSWORD):
    token = 'vk1.a.HkYvNXPyGv1Iztk1839GGZo-'\
            'EkwZLkrX8PeRvHWYcDK32anOUo8xUB2MQwEE2j6kce-'\
            'B3dKTwvuDp0bLCu9U4Zp19yKtRb' \
            '-TNsAJHGndx3SI0SPvzvTGBO6CS39_Jpp2JL4JypRT9SDwf9rQGJUh9l0x-'\
            'MUMm1d9GcwD-gWbgLjsPW5t1R2_uB2Dze1HPs5ghkoQmBzSC8VohlXRasZtLw'

    DSN = "{}://{}:{}@{}:{}/{}".format(DB_ENGINE, DB_USERNAME, DB_PASSWORD,
                                       DB_HOST, DB_PORT, DB_NAME)
    engine = sqlalchemy.create_engine(DSN)
    create_tables(engine)
    conn = Connect(engine)

    vk = vk_api.VkApi(token=token)
    longpoll = VkLongPoll(vk)
    last_candidate_for_users = {}

    keyboard = VkKeyboard()
    keyboard.add_button('Перейти к следующему',
                        color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('Добавить в избранное',
                        color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('Добавить в чёрный список',
                        color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('Список избранных',
                        color=VkKeyboardColor.PRIMARY)
    keyboard_2 = VkKeyboard()
    keyboard_2.add_button('Перейти к следующему',
                          color=VkKeyboardColor.PRIMARY)
    keyboard_2.add_line()
    keyboard_2.add_button('Список избранных',
                          color=VkKeyboardColor.PRIMARY)
    keyboard_3 = VkKeyboard()
    keyboard_3.add_button('Перейти к следующему',
                          color=VkKeyboardColor.PRIMARY)

    for event in longpoll.listen():

        if event.type == VkEventType.MESSAGE_NEW:

            if event.to_me:
                request = event.text
                pattern = re.compile(r'([12]), (\d{2}), ([а-яёА-ЯЁ\-]+)')

                if len(pattern.findall(request)) > 0:
                    info = request.split(', ')
                    user_gender = info[0]
                    user_age = info[1]
                    user_city_id_info = get_city_id(info[2], access_token)
                    if not user_city_id_info[0]:
                        write_simple_msg(vk, event.user_id,
                                         "Неверно введено название города!"
                                         "\nПопробуй ещё раз")
                    else:
                        user_city_id = user_city_id_info[1]
                        conn.session.add(User(vk_id=f'{event.user_id}',
                                              gender=int(user_gender),
                                              age=int(user_age),
                                              city_id=user_city_id))
                        searched_user_info = get_user_info(int(user_age),
                                                           int(user_gender),
                                                           user_city_id,
                                                           access_token,
                                                           event.user_id)
                        mes_res = create_message_for_candidate(
                                first_name=searched_user_info['first_name'],
                                last_name=searched_user_info['last_name'],
                                url_profile=searched_user_info['url_profile'])
                        write_simple_msg(vk, event.user_id,
                                         "Спасибо!\nЖелаю приятных знакомств!")
                        write_msg(vk=vk,
                                  user_id=event.user_id,
                                  message=f"{mes_res}",
                                  buttons=keyboard.get_keyboard(),
                                  attachment=searched_user_info['attachment'])
                        last_candidate_for_users[f'{event.user_id}'] = (
                                searched_user_info['first_name'],
                                searched_user_info['last_name'],
                                searched_user_info['url_profile'],
                                f"{searched_user_info['user_id']}")

                elif request == 'Перейти к следующему':
                    q = conn.session.query(User.user_id, User.age, User.gender,
                                           User.city_id). \
                                            select_from(User). \
                                            filter(User.vk_id ==
                                                   f'{event.user_id}').one()
                    user_id = q[0]
                    flag = 0
                    while flag == 0:
                        searched_user_info = get_user_info(q[1], q[2], q[3],
                                                           access_token,
                                                           event.user_id)
                        q_black_list = conn.session.query(
                            BlackList.block_vk_id). \
                            select_from(BlackList). \
                            filter(and_(BlackList.user_id == user_id,
                                        BlackList.block_vk_id ==
                                        f"{searched_user_info['user_id']}")).first()
                        q_favorite_list = conn.session.query(
                            Favorite.favorite_vk_id). \
                            select_from(Favorite). \
                            filter(and_(Favorite.user_id == user_id,
                                        Favorite.favorite_vk_id ==
                                        f"{searched_user_info['user_id']}")).first()
                        if q_black_list is None and q_favorite_list is None:
                            flag = 1
                    mes_res = create_message_for_candidate(
                            first_name=searched_user_info['first_name'],
                            last_name=searched_user_info['last_name'],
                            url_profile=searched_user_info['url_profile'])
                    write_msg(vk=vk,
                              user_id=event.user_id,
                              message=f"{mes_res}",
                              buttons=keyboard.get_keyboard(),
                              attachment=searched_user_info['attachment'])
                    last_candidate_for_users[f'{event.user_id}'] = (
                            searched_user_info['first_name'],
                            searched_user_info['last_name'],
                            searched_user_info['url_profile'],
                            f"{searched_user_info['user_id']}")
                elif request == 'Добавить в избранное':
                    candidate_info = last_candidate_for_users[f'{event.user_id}']
                    q_get_user_id = conn.session.query(User.user_id).filter(
                            User.vk_id == f'{event.user_id}').first()
                    user_id = q_get_user_id[0]
                    conn.session.add(Favorite(user_id=user_id,
                                              first_name=candidate_info[0],
                                              last_name=candidate_info[1],
                                              url_profile=candidate_info[2],
                                              favorite_vk_id=candidate_info[3]
                                              ))
                    conn.session.commit()
                    write_msg(vk=vk,
                              user_id=event.user_id,
                              message='Пользователь успешно добавлен в избранное!',
                              buttons=keyboard_2.get_keyboard())
                elif request == 'Добавить в чёрный список':
                    candidate_info = last_candidate_for_users[f'{event.user_id}']
                    q_get_user_id = conn.session.query(User.user_id).filter(
                            User.vk_id == f'{event.user_id}').first()
                    user_id = q_get_user_id[0]
                    conn.session.add(BlackList(user_id=user_id,
                                               block_vk_id=candidate_info[3]))
                    conn.session.commit()
                    write_msg(vk=vk,
                              user_id=event.user_id,
                              message='Пользователь добавлен в чёрный список',
                              buttons=keyboard_3.get_keyboard())
                elif request == 'Список избранных':
                    q_get_user_id = conn.session.query(User.user_id).filter(
                            User.vk_id == f'{event.user_id}').first()
                    user_id = q_get_user_id[0]
                    q = conn.session.query(Favorite.first_name,
                                           Favorite.last_name,
                                           Favorite.url_profile). \
                        select_from(Favorite). \
                        filter(Favorite.user_id == user_id).all()
                    if len(q) == 0:
                        write_msg(vk=vk,
                                  user_id=event.user_id,
                                  message='Список избранных пуст',
                                  buttons=keyboard_3.get_keyboard())
                    else:
                        mes_res = ''
                        for person in q:
                            mes_res += create_message_for_candidate(
                                    first_name=person[0],
                                    last_name=person[1],
                                    url_profile=person[2])
                            mes_res += '\n'
                        write_msg(vk=vk,
                                  user_id=event.user_id,
                                  message=mes_res,
                                  buttons=keyboard_3.get_keyboard())
                else:
                    write_simple_msg(vk=vk, user_id=event.user_id,
                                     message="Не понял вашего ответа...")
    conn.session.commit()


if __name__ == '__main__':
    access_token = ''
    DB_PORT = '5432'
    DB_NAME = ''
    DB_HOST = 'localhost'
    DB_ENGINE = 'postgresql'
    DB_USERNAME = 'postgres'
    DB_PASSWORD = ''
    run_bot(access_token, DB_PORT, DB_NAME, DB_HOST,
            DB_ENGINE, DB_USERNAME, DB_PASSWORD)
