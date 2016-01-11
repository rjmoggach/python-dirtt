import os
import grp
import pwd

__all__ = ['get_gid', 'get_uid', 'set_perms']


def get_group(group, default=0):
    """returns group struct for a group name or gid

    Example:
        >>> get_group('staff')
        grp.struct_group(gr_name='staff', gr_passwd='*', gr_gid=20, gr_mem=['root', 'wtguser'])
        >>> get_group(20)
        grp.struct_group(gr_name='staff', gr_passwd='*', gr_gid=20, gr_mem=['root', 'wtguser'])
    """
    if not group is None:
        try:
            if isinstance(group,int):
                group = grp.getgrgid(group)
            elif isinstance(group,basestring):
                group = grp.getgrnam(group)
        except:
            if isinstance(default,int):
                group = grp.getgrgid(default)
            elif isinstance(default,basestring):
                group = grp.getgrnam(default)
    return group


def get_user(user, default=0):
    """returns pwd struct for a given name string or id

    Example:
        >>> get_user('root')
        pwd.struct_passwd(pw_name='root', pw_passwd='*', pw_uid=0, pw_gid=0, pw_gecos='System Administrator', pw_dir='/var/root', pw_shell='/bin/sh')
        >>> get_user(0)
        pwd.struct_passwd(pw_name='root', pw_passwd='*', pw_uid=0, pw_gid=0, pw_gecos='System Administrator', pw_dir='/var/root', pw_shell='/bin/sh')
    """
    if not user is None:
        try:
            if isinstance(user,int):
                user = pwd.getpwuid(user)
            elif isinstance(user,basestring):
                user = pwd.getpwnam(user)
        except:
            if isinstance(default,int):
                user = pwd.getpwuid(default)
            elif isinstance(default,basestring):
                user = pwd.getpwnam(default)
    return user


def set_perms(target, perms, uid, gid):
    """
    given a provided permission, uid & gid
    set the the owner, group and permissions
    for a given path (directory, file, etc.)
    """
    assert target is not None
    assert perms is not None and isinstance(perms, int)
    assert uid is not None and isinstance(uid, int)
    os.chmod(target, perms)
    if uid and gid:
        os.chown(target,uid,gid)
    elif uid:
        os.chown(target,uid,0)
    else:
        return
