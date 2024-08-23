import functools
import traceback


def catch_exceptions(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            traceback.print_exc()
            return {"status": "fail", "message": "fail_message.internal_error"}, 500

    return wrapper
