from uuid import uuid4

import txaio
from autobahn.twisted.wamp import ApplicationSession
from crossbar.edge.worker.router import ExtRouterController
from twisted.internet.defer import ensureDeferred


class Main(ApplicationSession):

    def __init__(self, config=None):
        super().__init__(config)
        self.controller: ExtRouterController = config.controller
        self.worker = self.controller.config.extra.worker

    async def onJoin(self, details):
        await self.start_realms()

    async def start_realms(self, count=150000):
        gathered = []
        for i in range(count):
            config = self.get_realm_config(f"realm-{i}", "admin")
            gathered.append(ensureDeferred(self._start_realm(config)))

        await txaio.gather(gathered)

    def get_realm_config(self, name, role):
        realm_config = {"name": name}
        role_config = {
            "name": role,
            "permissions": [{
                "allow": {
                    "call": True,
                    "publish": True,
                    "register": True,
                    "subscribe": True
                },
                "match": "prefix",
                "uri": "foo.bar."
            }]
        }

        return {"realm_config": realm_config, "role_config": role_config}

    async def _start_realm(self, config):
        realm_config = config['realm_config']
        realm = realm_config['name']

        role_config = config["role_config"]
        role = role_config['name']

        proc = f'crossbar.worker.{self.worker}.start_router_realm'
        await self.controller.call(proc, realm, realm_config)
        proc = f'crossbar.worker.{self.worker}.start_router_realm_role'
        await self.controller.call(proc, realm, role, role_config)

        r2r = {
            "name": "router2router",
            "permissions": [
                {
                    "uri": "",
                    "match": "prefix",
                    "allow": {
                        "call": True,
                        "register": True,
                        "publish": True,
                        "subscribe": True
                    },
                    "disclose": {
                        "caller": True,
                        "publisher": True
                    },
                    "cache": True
                }
            ]
        }

        await self.controller.call(proc, realm, 'router2router', r2r)

        component_id = uuid4().__str__()
        component_config = {
            "id": component_id,
            "type": "class",
            "classname": "component.Main",
            "realm": realm,
            "role": role,
        }

        proc = f'crossbar.worker.{self.worker}.start_router_component'
        await self.controller.call(proc, component_id, component_config)
