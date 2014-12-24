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
import subprocess

from usersd.common import is_authorized, get_user

class User(usersd.objects.BaseObject):
	"""
	The User object
	"""
	
	interface_name = "org.semplicelinux.usersd.user"
	export_properties = [
		"user",
		"uid",
		"gid",
		"fullname",
		"address",
		"phone",
		"other",
		"home",
		"shell"
	]
	polkit_policy = "org.semplicelinux.usersd.modify-user"
	
	@staticmethod
	def add(user, fullname, shell="/bin/bash"):
		"""
		This static method adds a new user, using the useradd command.
		The arguments are self-explanatory.
		
		NOTE: the password will *NOT* encrypted, so you have to encrypt
		it *BEFORE* calling this method.
		
		Returns True if the user has been created successfully, False
		if not.
		"""
		
		if not subprocess.call((
			"useradd",
			user,
			"-m", # Create home directory
			"-U", # Create user group
			"-c", "%s,,,," % fullname, # Fullname
			"-s", shell, # Shell
		)):
			return True
		else:
			return False

	@usersd.objects.BaseObject.outside_timeout(
		"org.semplicelinux.usersd.user",
		sender_keyword="sender",
		connection_keyword="connection"
	)
	def ChangePassword(self, sender, connection):
		"""
		This method returns the object path for the given user.
		"""
		
		if self.polkit_policy and not is_authorized(
			sender,
			connection,
			self.polkit_policy,
			True # user interaction
		):
			raise Exception("E: Not authorized")
		
		# Check user
		if not get_user(sender) in (0, self.uid):
			raise Exception("E: Unable to change the password from another user")
		
		usersd.ui.ChangePasswordDialog().show(self)

	
	def change_password(self, newpassword, oldpassword=None):
		"""
		Changes the password.
		"""
		
		with open("/etc/shadow", "r") as f:
			lines = f.readlines()
		
		#
		#if not oldpassword:
		#	# New user!
		#	lines.append(":".join((
		#		self.user,
		#		"",
		#		"",
		#		
				
		
		with open("/etc/shadow", "w") as f:
			for line in lines:
				splt = line.split(":")
				if splt[0] == self.user:
					# Change
					splt[1] = newpassword
				
				f.write(":".join(splt))
	
	def __init__(self, bus_name, passwd_entry):
		"""
		Initializes the object.
		"""
		
		self.user, self.password, uid, gid, infos, self.home, self.shell = passwd_entry.split(":")
		
		# Parse GECOS
		infos = infos.split(",")
		self.fullname = self.address = self.phone = self.other = ""
		if len(infos) >= 1:
			self.fullname = infos[0]
		if len(infos) >= 2:
			self.address = infos[1]
		if len(infos) >= 3:
			self.phone = infos[2]
		if len(infos) >= 4:
			self.other = ",".join(infos[3:])
		
		self.uid = int(uid)
		self.gid = int(gid)
		
		self.path = "/org/semplicelinux/usersd/user/%s" % uid
		super().__init__(bus_name)
	
	def store_property(self, name, value):
		"""
		Stores the modified property in the /etc/passwd file.
		"""

		# Set value
		setattr(self, name[0].lower() + name[1:], value)
		
		# Save
		with open("/etc/passwd", "r") as f:
			# w+ doesn't seem to work lately...
			lines = f.readlines()
		
		with open("/etc/passwd", "w") as f:
			for line in lines:
				if line.split(":")[0] == self.user:
					# That's us!
					line = ":".join((
						self.user,
						self.password,
						str(self.uid),
						str(self.gid),
						",".join((
							self.fullname,
							self.address,
							self.phone,
							self.other
						)),
						self.home,
						self.shell
					)) + "\n"
				
				f.write(line)

