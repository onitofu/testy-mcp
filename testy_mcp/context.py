import contextvars


class RequestContext:
    _current_user: contextvars.ContextVar = contextvars.ContextVar("current_user", default=None)

    @classmethod
    def set(cls, user):
        cls._current_user.set(user)

    @classmethod
    def get(cls):
        return cls._current_user.get()
