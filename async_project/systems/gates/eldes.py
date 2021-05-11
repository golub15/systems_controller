import asyncio
import logging
import time

import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger("eldes")


class IEldes:
    def __init__(self, configs):
        self.cookies: aiohttp.cookiejar.CookieJar = None
        self.csrf = None
        self.next_ts_cookies = 0
        self.loop: asyncio.AbstractEventLoop
        self.session_semaphore = asyncio.Lock()

        self.config = configs
        pass

    async def get_status(self):
        resp = {'is_online': False,
                "broker": False}

        async with aiohttp.ClientSession() as session:
            async with session.get(
                    f"https://gates.eldesalarms.com/api1?id={self.config['DeviceId']}&key={self.config['api_token']}") as data:
                if data.status == 200:
                    resp['broker'] = True

                    json = await data.json()
                    if 'state' in json:
                        resp['is_online'] = json['state']
                    else:
                        logger.error("Cant parse eldes json")
                else:
                    resp['broker'] = False

        return resp

    async def user_db_update(self, data):

        async def fetch_user_data(id):
            ddd = await self.make_request(
                f"https://gates.eldesalarms.com/ru/gatesconfig/settings/users/ajax/1/device_id/{self.config['DeviceId']}/number/{id}")
            soup = BeautifulSoup(str(ddd), 'html.parser')
            try:
                phone_num = soup.find("input", {"id": "GatesconfigDeviceUsersdatabase_app_username"})['value']
                user_id = soup.find("input", {"id": "GatesconfigDeviceUsersdatabase_user_name"})['value']
            except Exception:
                return None
            return id, phone_num, user_id

        logger.debug('DB SYNC START')

        link = f"https://gates.eldesalarms.com/ru/gatesconfig/" \
               + f"settings/users/ajax/1/device_id/{self.config['DeviceId']}"

        reqs = []
        for i in range(1, data['last_count'] + 1):
            reqs.append(fetch_user_data(i))

        res = await asyncio.gather(*reqs)

        logger.debug(f'DB SYNC : FETCHED CURRENT USERS: {len(res)}')

        in_gates = list(filter(lambda x: x is not None, res))
        set_in_gates = list(map(lambda x: (x[1], x[2]), in_gates))

        add_list = set(data['users']) - set(set_in_gates)
        del_list = set(set_in_gates) - set(data['users'])

        def arc(phh):
            for idd, ph, tid in in_gates:
                if ph == phh:
                    return idd

        req_coro_list = []
        for nph, tid in del_list:
            user_id = arc(nph)
            rt2 = await self.make_request(
                f"https://gates.eldesalarms.com/"
                f"ru/gatesconfig/settings/usersdelete/ajax/1/device_id/"
                f"{self.config['DeviceId']}/number/{user_id}")

        logger.debug(f'DB SYNC : DELETED USERS: {len(del_list)}')

        cat = 'GatesconfigDeviceUsersdatabase'

        await self.update_session()
        req_add_coro_list = []
        for x in add_list:
            http_data = {
                "YII_CSRF_TOKEN": self.csrf,
                f"{cat}[phone]": x[0],
                f"{cat}[user_name]": x[1],
                f"{cat}[app]": "0",
                f"{cat}[app_password]": 111111,
                f"{cat}[output]": 1,
                f"{cat}[schedulerList]": "",
                f"{cat}[validuntildate]": "",
            }

            rr = await self.post_request(link, http_data)

        # res = await asyncio.gather(*req_add_coro_list)

        logger.debug(f'DB SYNC : ADDED USERS: {len(add_list)}')

        return True

    async def update_session(self):
        async with self.session_semaphore:

            if self.cookies is not None and time.time() < self.next_ts_cookies:
                return

            async with aiohttp.ClientSession() as session:
                async with session.get("https://gates.eldesalarms.com/en/user/login.html", ) as response:
                    ff: aiohttp.cookiejar.Morsel = response.cookies['YII_CSRF_TOKEN']
                    csrf = str(ff.value.split("%")[3][2:])
                    self.csrf = csrf

                    req_data = {
                        'YII_CSRF_TOKEN': csrf,
                        'UserLogin[username]': self.config['login'],
                        'UserLogin[password]': self.config['password']
                    }

                    async with session.post("https://gates.eldesalarms.com/en/user/login.html", data=req_data) as ss:
                        if ss.status == 200:
                            self.cookies = session.cookie_jar
                            self.next_ts_cookies = int(time.time()) + 3600

    async def post_request(self, link, data):
        await self.update_session()

        async with aiohttp.ClientSession(cookie_jar=self.cookies) as session:
            async with session.post(link, data=data) as response:
                return await response.text(encoding='utf-8')

    async def make_request(self, data):
        await self.update_session()

        async with aiohttp.ClientSession(cookie_jar=self.cookies) as session:
            async with session.get(data) as response:
                return await response.text(encoding='utf-8')

    async def update_events(self):

        x = [self.make_request(
            "https://gates.eldesalarms.com/ru/gatesconfig/settings/users/ajax/1/device_id/45830/number/204/tab/1.html")]

        r = await asyncio.gather(x)

        pass

    async def run(self):
        pass
