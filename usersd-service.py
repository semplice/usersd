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

from dbus.mainloop.glib import DBusGMainLoop

class Usersd(usersd.objects.BaseObject):
	"""
	The main object.
	"""
	
	path = "/org/semplicelinux/usersd"
	
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
		self._generate_users()
			
	def _generate_users(self):
		"""
		Generates a user object for every user in /etc/passwd.
		"""
				
		with open("/etc/passwd", "r") as f:
			for user in f:
				self._users[user.split(":")[0]] = usersd.user.User(self.bus_name, user.strip())
	
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
			raise Exception("E: Not authorized")
		
		return usersd.user.User.add(user, fullname)
		
	
if __name__ == "__main__":
		
	DBusGMainLoop(set_as_default=True)
	clss = Usersd()
	
	# Ladies and gentlemen...
	MainLoop.run()
