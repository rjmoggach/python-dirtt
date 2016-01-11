# -*- coding: utf-8 -*-
import errno
import numbers
import dirtt
from dirtt import LOG

__all__ = [ 'const', 'set_const' ]


def const(const):
    """Method that returns a package constant.

    This method is a convenience wrapper to yield the value of a constant
    based on module convention of importing constants as ``_c``.

    Args:
        const (str): constant name to retrieve from ``_c`` imported object

    Yields:
        int,str: the constant requested IF it exists

    Raises:

        DirttEnvError: if no such attribute exists

        TypeError: const is not a string or unicode object

    Example:

        >>> import dirtt
        >>> import dirtt.constants as _c
        >>> dirtt.const("DIRTT_VERSION")
        '3'

    .. seealso:: :const:`set_const`
    """
    try:
        return getattr(dirtt._c, const)
    except AttributeError:
        msg = u'No such constant: {0}'.format(const)
        dirtt.LOG.critical(msg)
        raise dirtt.exceptions.DirttEnvError(msg)
    except TypeError:
        msg = u'const name must be a string or unicode object, not: {0}'.format(const.__class__.__name__)
        dirtt.LOG.critical(msg)
        raise TypeError(msg)


def set_const(const, val):
    """Method that sets a dirtt constant.

    Convenience wrapper to reliably set the value of a constant
    from outside of package scope based on the module convention
    of importing/exporting constants as ``_c``

    Args:
        const (str): constant name to set
        val (str, int): value to set

    Yields:
        the constant set IF it is valid

    Raises:

        DirttEnvError: if no such attribute exists

        TypeError: val is not of correct type

    Example:

        >>> import dirtt
        >>> import dirtt.constants as _c
        >>> dirtt.set_const("DIRTT_VERSION", "4")
        "4"

    .. seealso:: :const:`const`
    .. warning:: const must exist (no new constants can be set)
    """
    try:
        cur = getattr(dirtt._c, const)
    except AttributeError:
        msg = u'no such constant: {0}'.format(const)
        dirtt.LOG.critical(msg)
        raise dirtt.exceptions.DirttEnvError(msg)
    except TypeError:
        msg = u'const name must be a string or unicode object, not: {0}'.format(const.__class__.__name__)
        dirtt.LOG.critical(msg)
        raise TypeError(msg)
    should_be = cur.__class__
    try:
        if not isinstance(val, should_be):
            if should_be is unicode or cur is None:
                val = val
            elif should_be is int and const.endswith('MODE'):
                val = int(val, 8)
            elif isinstance(cur, numbers.Integral):
                val = int(val)
            else:
                should_be(val)
    except (TypeError, ValueError, ):
        msg = u'invalid type for constant {0}, should be {1}, not: {2}'.format(const, should_be.__name__, val.__class__.__name__)
        dirtt.LOG.critical(msg)
        raise dirtt.exceptions.DirttEnvError(msg)
    setattr(dirtt._c, const, val)
    return val
