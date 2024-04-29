import requests
import random
import os
from dotenv import load_dotenv
from pprint import pprint


class UserVK:
    """
    The class allows you to find users by 
    specified criteria in the vk social network.

    Attributes:
    - age: int - the age of the user who performs the search
    - gender: int - the gender of the user who performs the search
    (0 - gender is not specified, 1 - female, 2 - male)
    - city_id: int - the ID of the city specified in the 
    profile of the user performing the search
    - token: str - the access_token for the vk social network
    - id: int - the id of the user performing the search. Default is None.

    """

    def __init__(self, age, gender, city_id, token, id=None):
        self.age = age
        self.gender = gender
        self.city_id = city_id
        self.token = token
        self.id = id

    def common_params(self):
        return {
            'access_token': self.token,
            'v': '5.199'
        }
    
    def __search_users_vk(self):
        """
        The method searches for users on the vk social network, 
        according to certain criteria (values from class attributes).

        The gender of the user for the search is reversed. If the 
        gender is not specified as "0", the gender is selected randomly.

        Returns: result of the search (code answer)

        """

        url = 'https://api.vk.com/method/users.search'
        if self.gender == 1:
            self.gender = 2
        elif self.gender == 2:
            self.gender = 1
        else:
            self.gender = random.randint(1, 2)
        params = self.common_params()
        params.update({
            'is_closed': False, 
            'sex': self.gender,
            'city': self.city_id,
            'age_from': self.age - 4,
            'age_to': self.age + 4,
            'has_photo': 1,
            'count': 1000,
        })
        response = requests.get(url, params=params)
        return response
    
    def get_user_info(self):
        """
        The method returns information about the user who fits the 
        search criteria.

        In addition, the selection is made so that the user's page is 
        open and the number of photos is 3 or more.

        Returns: dict with information about the user
        - id: int - the id of the user performing the search
        - user_id: int - the id of the user who meets the criteria
        - message: str - a message containing information about the 
        user who meets the search criteria (first name, last name, 
        link to the vk page)
        - attachment: str - a line with information about the three 
        most popular photos of the found user. In the form of attachment 
        ({type}{owner_id}_{media_id})

        """

        url = 'https://api.vk.com/method/photos.get'
        params = self.common_params()
        params.update({
            'owner_id': 0,
            'extended': 1,
            'album_id': 'profile',
        })
        users_info = self.__search_users_vk().json()\
            .get('response').get('items')
        random.shuffle(users_info)
        result = {
            'id' : self.id,
            'user_id': 0,
            'message': '',
            'attachment': '',
        }
        for user in users_info:
            if user.get('is_closed') is False:       #Add check blacklist users
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
                    
                    result['message'] += (f'Имя: {user.get("first_name")} '
                    f'Фамилия: {user.get("last_name")}\n'
                    f'Ссылка: https://vk.com/id{user.get("id")}')
                    result['user_id'] = user.get('id')
                    result['attachment'] = result.get('attachment').rstrip(',')
                    break
                else:
                    continue
        return result


if __name__ == "__main__":
    load_dotenv()
    token = os.getenv('TOKEN')
    user = UserVK(29, 2, 105, token)    #for example
    user_info = user.get_user_info()
    pprint(user_info)

        
                

