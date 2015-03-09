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

import usersd.objects
import usersd.ui
import subprocess

from usersd.common import is_authorized, get_user

from gi.repository import Gtk

MIN_PASSWORD_LENGTH = 4
USERNAME_ALLOWED_CHARS = "abcdefghijklmnopqrstuvwxyz0123456789.-"

class Group(usersd.objects.BaseObject):
	"""
	The User object
	"""
	
	interface_name = "org.semplicelinux.usersd.group"
	export_properties = [
		"group",
		"gid",
		"members",
	]
	polkit_policy = "org.semplicelinux.usersd.modify-user"
	
	def __init__(self, service, bus_name, group_entry):
		"""
		Initializes the object.
		"""
		
		self.service = service
		
		self.group, password, gid, members = group_entry.split(":")
		
		self.gid = int(gid)
		self.members = members.split(",")
		
		self.set_privileges = []
		
		self.path = "/org/semplicelinux/usersd/group/%s" % gid
		super().__init__(bus_name)
	
	def store_property(self, name, value):
		"""
		Stores the modified property in the /etc/passwd file.
		"""

		if name.lower() == "members":
			# Use gpasswd
			to_add = [user for user in value if not user in self.members]
			to_remove = [user for user in self.members if not user in value]
						
			if to_add:
				for user in to_add:
					subprocess.call((
						"gpasswd",
						self.group,
						"-a",
						user
					))
			
			if to_remove:
				for user in to_remove:
					subprocess.call((
						"gpasswd",
						self.group,
						"-d",
						user
					))
		else:
			# Not supported for now
			return

		# Set value
		setattr(self, name[0].lower() + name[1:], value)

