from tests.constants import BOT_ID


class MockBotInfo:
    def __init__(self, user_id: int = BOT_ID, username: str = "testbot") -> None:
        self.user_id = user_id
        self.username = username


class MockBot:
    def __init__(self, user_id: int = BOT_ID, username: str = "testbot") -> None:
        self.info = MockBotInfo(user_id, username)
