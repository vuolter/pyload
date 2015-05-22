# -*- coding: utf-8 -*-

import traceback


def deprecated(by=None):

    def wrapper(old_fn):

        def new(*args, **kargs):
            if by:
                new_fn = by
                args[0].core.log.debug(_('"%s" has been Deprecated, use "%s" instead.')
                    % (old_fn.__name__, new_fn.__name__))

                return new_fn(*args, **kargs)

            else:
                args[0].core.log.error(_('"%s" has been Removed.') % old_fn.__name__)
                traceback.print_exc()

        return new

    return wrapper


def lock(fn):

    def new(*args):
        # print "Handler: %s args: %s" % (fn, args[1:])
        args[0].lock.acquire()
        try:
            return fn(*args)

        finally:
            args[0].lock.release()

    return new


def read_lock(fn):

    def new(*args, **kwargs):
        args[0].lock.acquire(shared=True)
        try:
            return fn(*args, **kwargs)

        finally:
            args[0].lock.release()

    return new


def try_catch(fallback):
    """Decorator that executes the function and returns the value or fallback on any exception"""

    def wrapper(fn):

        def new(*args, **kwargs):
            try:
                return fn(*args, **kwargs)

            except Exception, e:
                args[0].core.log.error(_('Error executing "%s": %s') % (fn.__name__, str(e)))
                traceback.print_exc()
                return fallback

        return new

    return wrapper
