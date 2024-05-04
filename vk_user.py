import requests
import random


def common_params(token):
    return {
        'access_token': token,
        'v': '5.199'
    }


def get_city_id(city, token):
    url = 'https://api.vk.com/method/database.getCities'
    params = common_params(token)
    params.update({
        'q': city,
        'count': 1,
    })
    response = requests.get(url, params=params)
    if response.status_code == 200:
        city_resp = response.json().get('response').get('items')
        if len(city_resp) == 0:
            return (False, -1)
        else:
            city_id = city_resp[0].get('id')
        return (True, city_id)
    else:
        return (False, -1)


def search_users_vk(age, gender, city_id, token):
    """
    The function searches for users on the vk social network,
    according to certain criteria (values: age, gender, city_id).

    The gender of the user for the search is reversed. If the
    gender is not specified, the gender is selected randomly.

    Returns: result of the search (code answer)

    """

    url = 'https://api.vk.com/method/users.search'
    if gender == 1:
        gender = 2
    elif gender == 2:
        gender = 1
    else:
        gender = random.randint(1, 2)
    params = common_params(token)
    params.update({
        'is_closed': False,
        'sex': gender,
        'city': city_id,
        'fields': 'city',
        'age_to': age + 4,
        'has_photo': 1,
        'count': 200,
    })
    if 18 <= age <= 21:
        params.update({
            'age_from': 18,
        })
    if age > 21:
        params.update({
            'age_from': age - 4,
        })
    response = requests.get(url, params=params)
    return response


def get_user_info(age, gender, city_id, token, id):
    """
    The function returns information about the user who fits the
    search criteria.

    In addition, the selection is made so that the user's page is
    open and the number of photos is 3 or more.

    Returns: dict with information about the user
    - id: int - the id of the user performing the search
    - user_id: int - the id of the user who meets the criteria
    - first_name: str - first name of the
    user who meets the search criteria
    - last_name: str - last name of the
    user who meets the search criteria
    - url_profile: str - link to the vk page of the
    user who meets the search criteria
    - attachment: str - a line with information about the three
    most popular photos of the found user. In the form of attachment
    ({type}{owner_id}_{media_id})

    """

    url = 'https://api.vk.com/method/photos.get'
    params = common_params(token)
    params.update({
        'owner_id': 0,
        'extended': 1,
        'album_id': 'profile',
    })
    users_info = search_users_vk(age, gender, city_id, token).json() \
        .get('response').get('items')
    random.shuffle(users_info)
    result = {
        'id': id,
        'user_id': 0,
        'first_name': '',
        'last_name': '',
        'url_profile': '',
        'attachment': '',
    }
    for user in users_info:
        if user.get('is_closed') is False:
            try:
                f = (user.get('city')['id'] == city_id)
            except TypeError:
                continue
            if f:
                params['owner_id'] = user.get('id')
                response = requests.get(url, params=params).json()

                if response.get('response').get('count') >= 3:
                    photos = []

                    for photo in response.get('response').get('items'):
                        photo_info = [photo.get('owner_id'), photo.get('id'),
                                      photo.get('likes').get('count')]
                        photos.append(photo_info)
                    photos.sort(key=lambda x: x[2], reverse=True)
                    for photo in photos[:3]:
                        result['attachment'] += f'photo{photo[0]}_{photo[1]},'

                    result['first_name'] = user.get("first_name")
                    result['last_name'] = user.get("last_name")
                    result['url_profile'] = (f'https://vk.com/id'
                                             f'{user.get("id")}')
                    result['user_id'] = user.get('id')
                    result['attachment'] = result.get('attachment').rstrip(',')
                    break
                else:
                    continue
            else:
                continue
    return result
