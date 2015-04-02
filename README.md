usersd
======

usersd is a DBus activatable service that permits to manage and create
users and groups.

Design
------

Every user is exported as a separate DBus object, at the path:

	/org/semplicelinux/usersd/user/UID

where UID is the user's UID.

Properties (Full Name, Home directory, Address, etc) are exported through
DBus' standard Properties interface, but they aren't introspected due to
technical implications.

Properties are writeable, and they are syncronized automatically to /etc/passwd.

Likewise, every group is exported as a separate DBus object, too:

	/org/semplicelinux/usersd/group/GID

where GID is the group's GID.

Group members are exported as a property.

Security
--------

usersd runs as root, but requires Polkit authentication from the caller user
before actually doing things.

An exception is made for the caller user's object. Caller users can change
their properties and passwords as much as they want, but they can't delete
themselves.

To avoid sending password hashes through the system bus, the user creation and
password change methods are only available via a service-side GUI.
