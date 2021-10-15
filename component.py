from autobahn.twisted.wamp import ApplicationSession


class Main(ApplicationSession):
    async def onJoin(self, details):
        await self.register(self.echo, "foo.bar.echo")

    async def echo(self):
        return "ping"
