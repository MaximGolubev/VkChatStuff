import vk_requests
import os
import urllib.request
from configparser import ConfigParser

parser = ConfigParser()
parser.read('login_data.txt')

APP_ID = parser.get('login-section', 'APP_ID')
LOGIN = parser.get('login-section', 'LOGIN')
PASSWORD = parser.get('login-section', 'PASSWORD')
TARGET = parser.get('target-section', 'TARGET')


def type_priority(size_type):
    if size_type == 'w':
        return 9
    elif size_type == 'z':
        return 8
    elif size_type == 'y':
        return 7
    elif size_type == 'r':
        return 6
    elif size_type == 'q':
        return 5
    elif size_type == 'p':
        return 4
    elif size_type == 'o':
        return 3
    elif size_type == 'x':
        return 2
    elif size_type == 'm':
        return 1
    elif size_type == 's':
        return 0
    else:
        return -1

api = vk_requests.create_api(app_id=APP_ID,
                             login=LOGIN,
                             password=PASSWORD,
                             scope=['messages, users'],
                             api_version='5.80'
                             )

user = api.users.get(user_ids=TARGET)
print(user)
dir_name = 'E:/' + user[0]['first_name'] + user[0]['last_name'] + 'AllPhoto'
print(dir_name)
os.mkdir(path=dir_name)
start = 0
i = 0
while True:
    try:
        attach_pack = api.messages.getHistoryAttachments(peer_id=TARGET,
                                                         count=200,
                                                         media_type='photo',
                                                         start_from=start,
                                                         fields='first_name')
        items = attach_pack['items']
        if not items:
            break
        start = attach_pack['next_from']
        for item in items:
            sizes = item['attachment']['photo']['sizes']
            sizes.sort(key=lambda x: type_priority(x['type']), reverse=True)
            urllib.request.urlretrieve(sizes[0]['url'], dir_name + '/' + str(i) + '.jpg')
            i += 1
    except vk_requests.exceptions.VkAPIError:
        continue





