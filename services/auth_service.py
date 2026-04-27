class AuthService:
    def login(self, email_or_username: str, password: str):
        # TODO: implementasi login dengan DB
        return {"username": email_or_username}

    def register(self, username: str, email: str, password: str):
        # TODO: implementasi register dengan DB
        return True, None
