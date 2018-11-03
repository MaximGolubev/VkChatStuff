import vk_requests
import os
import urllib.request
from configparser import ConfigParser
from multiprocessing import Pool as ProcessPool
from dataclasses import dataclass
import time


@dataclass
class VkSaverParams:
    app_id: str = None
    login: str = None
    password: str = None
    target_id: str = None
    version: str = '5.87'

    def is_valid(self):
        return self.app_id is not None and \
               self.login is not None and \
               self.password is not None and \
               self.target_id is not None

    def from_ini_file(self,
                      params_path: str
                      ):
        ini_parser = ConfigParser()
        try:
            ini_parser.read(params_path)
            self.app_id = ini_parser.get('login-section', 'APP_ID')
            self.login = ini_parser.get('login-section', 'LOGIN')
            self.password = ini_parser.get('login-section', 'PASSWORD')
            self.target_id = ini_parser.get('target-section', 'TARGET')
        except Exception:
            pass
        return self.is_valid()


class VkStuffSaver:
    def __init__(self,
                 params: VkSaverParams = None,
                 params_path: str = None
                 ):
        if params is not None and params.is_valid():
            self.params = params
            try:
                self._api = vk_requests.create_api(app_id=params.app_id,
                                                   login=params.login,
                                                   password=params.password,
                                                   api_version=params.version,
                                                   scope=['messages', 'users'])
            except vk_requests.exceptions.VkAPIError:
                self._api = None

        if params is None:
            self.params = VkSaverParams()
            self.params.from_ini_file(params_path=params_path)
            try:
                self._api = vk_requests.create_api(app_id=self.params.app_id,
                                                   login=self.params.login,
                                                   password=self.params.password,
                                                   api_version=self.params.version,
                                                   scope=['messages', 'users'])
            except vk_requests.exceptions.VkAPIError:
                self._api = None

    def set_params(self,
                   params: VkSaverParams
                   ):
        if not params.is_valid():
            return False
        self.params = params
        try:
            self._api = vk_requests.create_api(app_id=params.app_id,
                                               login=params.login,
                                               password=params.password,
                                               api_version=params.version,
                                               scope=['messages', 'users'])
        except vk_requests.exceptions.VkAPIError:
            pass
        return True

    @staticmethod
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

    @staticmethod
    def to_processes(links: list, dir_name: str, proc_num: int):
        delta = int(len(links) / proc_num)
        bounds = [(i * delta, (i + 1) * delta)
                  for i in range(proc_num)
                  if i != proc_num - 1]
        bounds.append(((proc_num - 1) * delta, len(links)))

        pool = ProcessPool(processes=proc_num)
        for i in range(proc_num):
            pool.apply_async(VkStuffSaver.save_links,
                             (links[bounds[i][0]:bounds[i][1]], dir_name))
        pool.close()
        pool.join()

    @staticmethod
    def save_link(link: tuple, dir_name: str):
        year, month = time.strftime("%Y_%m",
                                    time.gmtime(link[1]['date'])).split('_')
        subdirectory = dir_name + '/' + year
        if not os.path.exists(subdirectory):
            os.mkdir(path=subdirectory)

        subdirectory += ('/' + month)
        if not os.path.exists(subdirectory):
            os.mkdir(path=subdirectory)

        name = str(link[1]['date']) + '_' + str(link[2])
        file_name = subdirectory + '/' + name + '.jpg'
        urllib.request.urlretrieve(link[0], file_name)

    @staticmethod
    def save_links(links: list, dir_name: str):
        for link in links:
            VkStuffSaver.save_link(link, dir_name)

    def _get_links_pack(self,
                        media_type: str,
                        start_pos: int,
                        start_date: str,
                        end_date: str):
        links = []
        peer_id = self.params.target_id
        attach_pack = self._api.messages.getHistoryAttachments(peer_id=peer_id,
                                                               count=200,
                                                               media_type=media_type,
                                                               start_from=start_pos)
        items = attach_pack['items']
        try:
            next_pos = attach_pack['next_from']
        except KeyError:
            next_pos = None

        for item in items:
            sizes = item['attachment']['photo']['sizes']
            sizes.sort(key=lambda x: self.type_priority(x['type']),
                       reverse=True)
            url = sizes[0]['url']
            links.append((url,
                          {
                              'date': item['attachment']['photo']['date'],
                              'size': (sizes[0]['width'], sizes[0]['height'])
                          },
                          item['attachment']['photo']['id']
                          )
                         )
        return next_pos, links

    def save_attachments(self,
                         media_type='photo',
                         start_date=None,
                         end_date=None,
                         output_dir=None):
        directory = output_dir
        if not output_dir:
            user_name = self._api.users.get(user_ids=self.params.target_id)[0]
            directory = 'id' + \
                        self.params.target_id + \
                        '_' + \
                        user_name['first_name'] + \
                        '_' + \
                        user_name['last_name']

        if not os.path.exists(directory):
            os.mkdir(path=directory)

        start = 0
        links = []

        while True:
            try:
                start, links_pack = self._get_links_pack(media_type=media_type,
                                                         start_pos=start,
                                                         start_date='0',
                                                         end_date='0')
                links.extend(links_pack)
                if start is None:
                    break
            except vk_requests.exceptions.VkAPIError:
                if links:
                    link = links.pop(0)
                    VkStuffSaver.save_link(link, directory)
                continue

        self.to_processes(links=links,
                          dir_name=directory,
                          proc_num=16)


if __name__ == "__main__":
    saver = VkStuffSaver(params_path='login_data.txt')
    saver.save_attachments(media_type='photo',
                           output_dir="E:/AlexFokinPhoto")
