import vk_requests
from configparser import ConfigParser

parser = ConfigParser()
parser.read('login_data.txt')

APP_ID = parser.get('login-section', 'APP_ID')
LOGIN = parser.get('login-section', 'LOGIN')
PASSWORD = parser.get('login-section', 'PASSWORD')
TARGET = parser.get('target-section', 'TARGET')


api = vk_requests.create_api(app_id=APP_ID,
                             login=LOGIN,
                             password=PASSWORD,
                             scope=['messages'])

history = []
count = api.messages.getHistory(offset=0, count=0, user_id='95744413')['count']
offset = 0
while offset < count:
    history.append(api.messages.getHistory(offset=offset, count=200, user_id=TARGET)['items'])
    offset += 200
    print(history)




