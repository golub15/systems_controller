from abc import ABC

import time
from async_project.core.eventbus import *
from async_project.systems.base.system import System
from async_project.systems.gates.eldes import IEldes

logger = logging.getLogger("gates")



class Gates(System, ABC):

    def __init__(self, bus: EventBus, uid: str, db, conf: dict):
        super().__init__(bus, uid, db, conf)

        self.obj_id = self.conf['object_id']
        self.home_max_id = self.conf['home_max_id']
        self.module_gates = IEldes(self.conf['auth'])

        self.states = {
            "last_sync_ts": "",
            "user_db_is_changed": 0,
            "user_db_ts_changed": 1,
            "last_count_users": 182,
            "last_event_ts": "",
            "status": {
                "broker": False,
                "is_online": False,
                "last_time_seen": -1,
                "day_count": -1

            }
        }

    def btpp(self, val):
        if val:
            return '✅'
        else:
            return '❌'

    async def update_status(self):
        while 1:
            await asyncio.sleep(5)

            status = {}
            try:
                status = await self.module_gates.get_status()
            except Exception as msg:
                logger.error(f'Failed get status at:{msg}')
                status["broker"] = False
                status["is_online"] = False

            if status["broker"] != self.states["status"]["broker"]:
                self.states["status"]["broker"] = status["broker"]

                if not status["broker"]:
                    await self.send_notify('Авария сервиса посредника')
                else:
                    await self.send_notify('Подключен к сервису посредника')
            if status["is_online"] != self.states["status"]["is_online"]:
                self.states["status"]["is_online"] = status["is_online"]

                if not status["is_online"]:
                    await self.send_notify('Авария связи')
                    self.states["status"]["last_time_seen"] = int(time.time())
                else:
                    await self.send_notify('Связь востановлена')

            # ft = await self.module_gates.make_request(
            #   'https://gates.eldesalarms.com/ru/gatesconfig/settings/getlog/ajax/1/device_id/45830.html?_=1618050546877&logstart=2020-10-18&logend=')
            # ft22 = await self.module_gates.make_request(f'https://gates.eldesalarms.com' + ft.split('"')[13])
            # print(ft22)

    async def events_sync_task(self):
        while 1:
            await asyncio.sleep(5)
            # await self.send_notify(f"Test notify: {int(time.time())}")

            # start_ts = self.states['last_event_ts']
            # # events = await self.module_gates(start_ts, end_ts)
            # events = None
            # e = {
            #     "ts": 123,
            #     "type": "",
            #     "value": ""
            # }
            # for event in events:
            #     if event["type"] == "call":
            #         pass

    async def db_sync_task(self):
        while 1:
            await asyncio.sleep(5)
            if not self.states['status']['broker']:
                continue

            if self.states['user_db_is_changed']:
                if self.states['user_db_ts_changed'] + 5 < time.time():
                    try:
                        sql = """SELECT phone, home_id FROM users WHERE obj_id == :oid
                                UNION ALL
                                SELECT phone, 'worker' FROM company_users"""
                        resp1 = await self.db.fetch_all(query=sql,
                                                        values={"oid": self.obj_id})
                        norm = []
                        for k, v in resp1:
                            norm.append((str(k), str(v)))

                        data = {
                            "last_count": self.states['last_count_users'],
                            "users": norm
                        }

                        result = await self.module_gates.user_db_update(data)
                        if result:
                            logger.info("User db is sync success")
                            await self.send_notify('User db is sync success')
                            self.states['user_db_is_changed'] = 0
                            self.states['last_count_users'] = len(norm)
                    except Exception as msg:
                        logger.error(f"User db is sync failed at: {msg}")
                        self.states['user_db_ts_changed'] = int(time.time()) + 60

    async def run(self):
        await self.loads_states()
        self.loop.create_task(self.state_observator())

        self.loop.create_task(self.db_sync_task())
        self.loop.create_task(self.update_status())
        self.loop.create_task(self.events_sync_task())

    async def bot_commands(self, req):
        fsm = req['fsm']
        resp = {}
        if req['type'] == 'text':
            if len(fsm) > 0:
                if fsm[-1][0] == 'db':

                    try:
                        home_id = int(req["data"])
                        if 0 < home_id > self.home_max_id:
                            raise ValueError
                        resp['fsm_add'] = ('id', home_id, f"Кв: {home_id}")
                        resp['menu_update'] = 0
                    except ValueError:
                        pass

        return resp

    async def get_users(self, home_id=None):
        resp = await self.db.fetch_all(
            query=f"SELECT phone, name, (SELECT title FROM roles WHERE id == role_id), call_ack, last_call"
                  " FROM users"
                  " WHERE obj_id == :obj_id AND home_id == :home_id",
            values={"obj_id": self.obj_id, "home_id": home_id})

        return resp

    async def bot_menu(self, fsm):
        r = {}

        if len(fsm) == 0:
            r['text'] = 'Меню системы ворот \nВыберите действие'
            r['buttons'] = [('🧩 База данных', 'db', '-1'),
                            ('🧩 Sync БД', 'db_sync', '-1'),
                            ('🧩 Состояние', 'status', '-1'),
                            ('🧩 Cобытия', 'history', '-1'),
                            ('🧩 Настройки', 'configs', '-1')]
            r['row_width'] = 3
        else:
            point_type = fsm[0][0]
            point_id = fsm[0][1]

            if point_type == 'db':

                if len(fsm[1:]) == 0:
                    r['text'] = 'Меню базы данных ворот \nВыберите квартиру, набрав <u>номер</u>'
                    r['row_width'] = 2
                else:
                    point_type = fsm[1][0]
                    point_id = fsm[1][1]

                    if point_type == 'id':
                        users = await self.get_users(home_id=int(point_id))
                        rr = []
                        ui = 1
                        for phone, name, role, call_ack, last_call in users:
                            if call_ack:
                                clk = '✅'
                            else:
                                clk = '❌'
                            phone = str(phone)
                            np = f"{phone[0]} ({phone[1:4]}) {phone[4:7]}-{phone[7:9]}-{phone[9:11]}"
                            rr.append(f"{ui}.{role}{clk} <b>{np}</b> {name} - {last_call}")
                            ui += 1

                        if len(rr) != 0:
                            tt = "\n".join(rr)
                        else:
                            tt = 'Нет записей'
                        r['text'] = 'Меню квартиры: \n\n' + tt
                        r['row_width'] = 2
            if point_type == 'status':
                tm1 = f"Связь с брокером: {self.btpp(self.states['status']['broker'])}"
                tm2 = f"Связь с модулем ворот: {self.btpp(self.states['status']['is_online'])}"
                tm3 = f"Ожидание синхронизации: {self.btpp(self.states['user_db_is_changed'])}"

                r['text'] = f'Состояние ворот \n{tm1}\n{tm2}\n{tm3}'
                r['row_width'] = 2
            if point_type == 'db_sync':
                self.states['user_db_is_changed'] = 1
                self.states['user_db_ts_changed'] = int(time.time())
        # btn ('Text', 'type', 'id')

        return r
