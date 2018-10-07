import vk_requests
import os
import urllib.request
from configparser import ConfigParser
from multiprocessing import Pool as ProcessPool
import re

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


def save_links(links: list, dir_name: str):
    for link in links:
        name = re.sub(r'[^[a-zA-z0-9]', '', link)
        file_name = dir_name + '/' + name + '.jpg'
        urllib.request.urlretrieve(link, file_name)


def to_processes(links: list, dir_name: str, proc_num: int):
    delta = int(len(links) / proc_num)
    bounds = [(i * delta, (i + 1) * delta) for i in range(proc_num)]
    pool = ProcessPool(processes=proc_num)
    for i in range(proc_num):
        pool.apply_async(save_links,
                         (links[bounds[i][0]:bounds[i][1]], dir_name))
    pool.close()
    pool.join()


if __name__ == "__main__":
    api = vk_requests.create_api(app_id=APP_ID,
                                 login=LOGIN,
                                 password=PASSWORD,
                                 scope=['messages, users'],
                                 api_version='5.80'
                                 )

    user = api.users.get(user_ids=TARGET)
    print(user)
    dir_name = 'E:/' + user[0]['first_name'] + user[0]['last_name'] + 'AllPhoto'
    if not os.path.exists(dir_name):
        print(dir_name)
        os.mkdir(path=dir_name)
    start = 0
    links = []
    print("START")
    while True:
        try:
            attach_pack = api.messages.getHistoryAttachments(peer_id=TARGET,
                                                             count=200,
                                                             media_type='photo',
                                                             start_from=start)
            items = attach_pack['items']
            if not items:
                break
            start = attach_pack['next_from']
            for item in items:
                sizes = item['attachment']['photo']['sizes']
                sizes.sort(key=lambda x: type_priority(x['type']), reverse=True)
                links.append(sizes[0]['url'])

        except vk_requests.exceptions.VkAPIError:
            if links:
                url = links.pop(0)
                file_name = dir_name + '/' + url.replace('/', '') + '.jpg'
                urllib.request.urlretrieve(url, file_name)
            continue

    print(len(links))
    to_processes(links, dir_name, 20)




