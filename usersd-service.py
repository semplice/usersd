#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# usersd - user management daemon
# Copyright (C) 2014  Eugenio "g7" Paolantonio
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#
# Authors:
#    Eugenio "g7" Paolantonio <me@medesimo.eu>
#

import os

import dbus

from usersd.common import MainLoop, is_authorized

import usersd.objects
import usersd.user
import usersd.group

import quickstart.translations

from dbus.mainloop.glib import DBusGMainLoop

if os.path.islink(__file__):
	# If we are a link, everything is a WTF...
	USERSD_DIR = os.path.dirname(os.path.normpath(os.path.join(os.path.dirname(__file__), os.readlink(__file__))))
else:
	USERSD_DIR = os.path.dirname(__file__)


# While the following is not ideal, is currently needed to make sure
# we are actually on the main vera-control-center directory.
# The main executable (this) and all modules do not use absolute paths
# to load the glade UI files, so we need to be on the main directory
# otherwise they will crash.
# This should be probably addressed directly in quickstart.builder but,
# for now, this chdir call will do the job.
os.chdir(USERSD_DIR)

# Parse default locale from /etc/default/locale
try:
	with open("/etc/default/locale", "r") as f:
		os.environ["LANG"] = f.readline().strip().split("=")[-1]
except:
	pass

TRANSLATION = quickstart.translations.Translation("usersd")
TRANSLATION.load()
TRANSLATION.install()
TRANSLATION.bind_also_locale()

class Usersd(usersd.objects.BaseObject):
	"""
	The main object.
	"""
	
	path = "/org/semplicelinux/usersd"
	
	@dbus.service.signal(
		"org.semplicelinux.usersd.user"
	)
	def UserListChanged(self):
		"""
		Signal emitted when the user list has been changed.
		"""
		
		pass
	
	def __init__(self):
		"""
		Initializes the object.
		"""
		
		self.bus_name = dbus.service.BusName(
			"org.semplicelinux.usersd",
			bus=dbus.SystemBus()
		)
		
		super().__init__(self.bus_name)
		
		self._users = {}
		self._groups = {}
		self._generate_users(refresh_groups=False)
		self._generate_groups()
	
	def _generate_users(self, refresh_groups=True):
		"""
		Generates a user object for every user in /etc/passwd.
		"""
				
		with open("/etc/passwd", "r") as f:
			for user in f:
				name = user.split(":")[0]
				if not name in self._users:
					self._users[name] = usersd.user.User(
						self,
						self.bus_name,
						user.strip()
					)
		
		# Refresh groups if asked to
		if refresh_groups:
			self._generate_groups()
		
		# Emit signal
		self.UserListChanged()
	
	def _generate_groups(self, refresh=False):
		"""
		Generates a group object for every group in /etc/group.
		"""
		
		with open("/etc/group", "r") as f:
			for group in f:
				name = group.split(":")[0]
				if not name in self._groups:
					self._groups[name] = usersd.group.Group(
						self,
						self.bus_name,
						group.strip()
					)
				elif refresh:
					self._groups[name].refresh_members_from_group_entry(group.strip())
	
	def remove_from_user_list(self, user):
		"""
		Removes the given username from the users list.
		"""
		
		if user in self._users:
			del self._users[user]

		# Refresh groups
		self._generate_groups(refresh=True)
		
		# Emit signal
		self.UserListChanged()

	@usersd.objects.BaseObject.outside_timeout(
		"org.semplicelinux.usersd.group",
		out_signature="a{i(s)}",
		sender_keyword="sender",
		connection_keyword="connection"
	)
	def GetGroups(self, sender, connection):
		"""
		This method returns a dictionary containing every group's GID as keys,
		and the groupname as values.
		"""
		
		result = {}
					
		for group, obj in self._groups.items():
			result[obj.gid] = (group,)
		
		return result

	@usersd.objects.BaseObject.outside_timeout(
		"org.semplicelinux.usersd.group",
		in_signature="s",
		out_signature="as",
		sender_keyword="sender",
		connection_keyword="connection"
	)
	def GetGroupsForUser(self, user, sender, connection):
		"""
		This method returns an array containing every group the given
		user is in.
		"""
		
		result = []
					
		for group, obj in self._groups.items():
			if user in obj.members:
				result.append(group)
		
		return result

	@usersd.objects.BaseObject.outside_timeout(
		"org.semplicelinux.usersd.group",
		in_signature="s",
		out_signature="s",
		sender_keyword="sender",
		connection_keyword="connection"
	)
	def LookupGroup(self, group, sender, connection):
		"""
		This method returns the object path for the given group.
		"""
		
		if group in self._groups: return self._groups[group].path
		
		return None
	
	# NOTE: The following method needs to be properly security-audited
	# before we can export it to DBus.
	# For now is only meant to be used internally when creating an user.
	# You can take advantage of that using the ShowUserCreationUI method.
	#
	#@usersd.objects.BaseObject.outside_timeout(
	#	"org.semplicelinux.usersd.user",
	#	in_signature="sas",
	#	sender_keyword="sender",
	#	connection_keyword="connection"
	#)
	def AddGroupsToUser(self, user, groups, sender=None, connection=None):
		"""
		Adds the given user to every group specified in the specfied
		groups list.
		"""
		
		if sender and connection and not is_authorized(
			sender,
			connection,
			"org.semplicelinux.usersd.add-user",
			True # user interaction
		):
			raise Exception("Not authorized")
		
		for group in groups:
			if not group in self._groups:
				continue
			
			members = self._groups[group].members
			if not user in members:
				members.append(user)
			
				self._groups[group].Set(
					"org.semplicelinux.usersd.group",
					"Members",
					members
				)
	
	def get_uids_with_users(self):
		"""
		A variant of the self._users dictionary, with UIDs as keys.
		"""
		
		result = {}
		
		for user, obj in self._users.items():
			
			result[obj.uid] = obj
		
		return result

	@usersd.objects.BaseObject.outside_timeout(
		"org.semplicelinux.usersd.user",
		out_signature="a{i(sss)}",
		sender_keyword="sender",
		connection_keyword="connection"
	)
	def GetUsers(self, sender, connection):
		"""
		This method returns a dictionary containing every user's UID as keys,
		and the username with the full name as values.
		"""
		
		result = {}
					
		for user, obj in self._users.items():
			result[obj.uid] = (user, obj.fullname, obj.home)
		
		return result

	@usersd.objects.BaseObject.outside_timeout(
		"org.semplicelinux.usersd.user",
		in_signature="s",
		out_signature="s",
		sender_keyword="sender",
		connection_keyword="connection"
	)
	def LookupUser(self, user, sender, connection):
		"""
		This method returns the object path for the given user.
		"""
		
		if user in self._users: return self._users[user].path
		
		return None

	@usersd.objects.BaseObject.outside_timeout(
		"org.semplicelinux.usersd.user",
		in_signature="ss",
		out_signature="b",
		sender_keyword="sender",
		connection_keyword="connection"
	)
	def CreateUser(self, user, fullname, sender, connection):
		"""
		This method returns the object path for the given user.
		"""
		
		if not is_authorized(
			sender,
			connection,
			"org.semplicelinux.usersd.add-user",
			True # user interaction
		):
			raise Exception("Not authorized")
		
		if usersd.user.User.add(user, fullname):
			# User created successfully, we should refresh the user list
			self._generate_users()
	
	@usersd.objects.BaseObject.outside_timeout(
		"org.semplicelinux.usersd.user",
		in_signature="sas",
		sender_keyword="sender",
		connection_keyword="connection"
	)
	def ShowUserCreationUI(self, display, groups, sender, connection):
		"""
		This method shows the user interface that permits to create a new
		user.
		"""
		
		if not is_authorized(
			sender,
			connection,
			"org.semplicelinux.usersd.add-user",
			True # user interaction
		):
			raise Exception("Not authorized")
		
		usersd.user.User.add_graphically(sender, self, display, groups)
	
if __name__ == "__main__":
		
	DBusGMainLoop(set_as_default=True)
	clss = Usersd()
	
	# Ladies and gentlemen...
	MainLoop.run()
