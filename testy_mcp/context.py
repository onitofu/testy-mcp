import contextvars


class RequestContext:
    _current_user: contextvars.ContextVar = contextvars.ContextVar("current_user", default=None)
    _current_scopes: contextvars.ContextVar = contextvars.ContextVar("current_scopes", default=None)

    @classmethod
    def set(cls, user, scopes=None):
        cls._current_user.set(user)
        cls._current_scopes.set(scopes)

    @classmethod
    def get(cls):
        return cls._current_user.get()

    @classmethod
    def scopes(cls):
        return cls._current_scopes.get()
