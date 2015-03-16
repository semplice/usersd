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

import dbus

from usersd.common import MainLoop, is_authorized

import usersd.ui
import usersd.objects
import usersd.user
import usersd.group

from dbus.mainloop.glib import DBusGMainLoop

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
		sender_keyword="sender",
		connection_keyword="connection"
	)
	def ShowUserCreationUI(self, sender, connection):
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
		
		usersd.user.User.add_graphically(self)
	
if __name__ == "__main__":
		
	DBusGMainLoop(set_as_default=True)
	clss = Usersd()
	
	# Ladies and gentlemen...
	MainLoop.run()
