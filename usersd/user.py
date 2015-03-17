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

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=[
	"md5_crypt",
	"bcrypt",
	"sha1_crypt",
	"sun_md5_crypt",
	"sha256_crypt",
	"sha512_crypt",
])

default_encryption = "sha512_crypt"

MIN_PASSWORD_LENGTH = 4
USERNAME_ALLOWED_CHARS = "abcdefghijklmnopqrstuvwxyz0123456789.-"

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
		
		if subprocess.call((
			"useradd",
			user,
			"-m", # Create home directory
			"-U", # Create user group
			"-c", "%s,,,," % fullname, # Fullname
			"-s", shell, # Shell
		)) == 0:
			return True
		else:
			return False
	
	@staticmethod
	def add_graphically(service, groups=[]):
		"""
		This static method allows the end-user to add a new user account.
		It differs from the add() method because this one uses a GTK+ Dialog
		to prompt the user for the required fields.
		
		It's useful for distributors who need to implement a graphical user
		management tool.
		"""
		
		# Create add_user_dialog
		add_user_dialog = usersd.ui.AddUserDialog()
		
		# Connect response
		add_user_dialog.connect("response", User.on_add_user_dialog_response, add_user_dialog, service, groups)
		
		add_user_dialog.show()
	
	@staticmethod
	def on_add_user_dialog_response(dialog, response, parent, service, groups):
		"""
		Fired when a button on the add_user_dialog has been clicked.
		"""
		
		if response == Gtk.ResponseType.OK:
			# Ensure nothing is empty
			for obj in ("fullname", "username", "password", "confirm_password"):
				if parent.objects[obj].get_text() == "":
					parent.show_error("Please complete the entire form.")
					return False

			username = parent.objects.username.get_text()
			
			# Verify that the specified username is unique
			if username in service._users:
				parent.show_error("The username '%s' is already taken." % username)
				return False
			
			# Verify that the specified username doesn't contain unallowed chars
			unallowed = []
			for char in username:
				if char not in USERNAME_ALLOWED_CHARS and char not in unallowed:
					unallowed.append(char)
			if unallowed:
				parent.show_error("The username must not contain the following characters: %s" % unallowed)
				return False
			
			# Verify passwords
			if not parent.objects.password.get_text() == parent.objects.confirm_password.get_text():
				parent.show_error("The passwords do not match.")
				return False
			
			# Check password length
			if not len(parent.objects.password.get_text()) >= MIN_PASSWORD_LENGTH:
				parent.show_error("The password should be of at least %s characters." % MIN_PASSWORD_LENGTH)
				return False
			
			parent.hide_error()
						
			# Add the user
			if not User.add(username, parent.objects.fullname.get_text()):
				parent.show_error("Something went wrong while creating the new user.")
				return False
			
			# Add the user to the specified default groups
			service.AddGroupsToUser(username, groups)
			
			# Refresh
			service._generate_users()
			
			# Lookup for the newly created user
			if not username in service._users:
				parent.show_error("Something went wrong while creating the new user.")
				return False
			
			# Set password
			service._users[username].change_password(parent.objects.password.get_text())
			
		# Destroy the window
		dialog.destroy()
	
	@usersd.objects.BaseObject.outside_timeout(
		"org.semplicelinux.usersd.user",
		in_signature="b",
		out_signature="b",
		sender_keyword="sender",
		connection_keyword="connection"
	)
	def DeleteUser(self, with_home, sender, connection):
		"""
		Deletes the user.
		If with_home is True, the user's home directory will be deleted as well.
		
		Returns True if the user has been deleted successfully, False if not.
		"""
		
		if get_user(sender) == self.uid:
			# The sender can't remove itself!
			raise Exception("The sender can't remove itself!")
		
		if self.polkit_policy and not is_authorized(
			sender,
			connection,
			self.polkit_policy,
			True # user interaction
		):
			raise Exception("Not authorized")
		
		deluser_call = ["deluser", self.user]
		
		# deluser is picky with blank arguments, so we can't put an ""
		# in the place of --remove-home
		if with_home:
			deluser_call.append("--remove-home")
		
		if subprocess.call(deluser_call) == 0:
			self.service.remove_from_user_list(self.user)
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
		
		if not get_user(sender) in self.set_privileges and (self.polkit_policy and not is_authorized(
			sender,
			connection,
			self.polkit_policy,
			True # user interaction
		)):
			raise Exception("Not authorized")
		
		# Create changepassword dialog
		change_password_dialog = usersd.ui.ChangePasswordDialog(self.is_locked())
		
		# Connect response
		change_password_dialog.connect("response", self.on_change_password_dialog_response, change_password_dialog)
		
		change_password_dialog.show()

	def on_change_password_dialog_response(self, dialog, response, parent):
		"""
		Fired when a button on the change_password_dialog has been clicked.
		"""
		
		if response == Gtk.ResponseType.OK:
			# Verify old password
			if not parent.locked and not self.verify_password(parent.objects.old_password.get_text()):
				parent.show_error("Current password is not correct.")
				return False
			
			# Verify new passwords
			if not parent.objects.new_password.get_text() == parent.objects.confirm_new_password.get_text():
				parent.show_error("The new passwords do not match.")
				return False
			
			# Check password length
			if not len(parent.objects.new_password.get_text()) >= MIN_PASSWORD_LENGTH:
				parent.show_error("The new password should be of at least %s characters." % MIN_PASSWORD_LENGTH)
				return False
			
			parent.hide_error()
			
			# Finally set password
			self.change_password(parent.objects.new_password.get_text())
			
		# Destroy the window
		dialog.destroy()
	
	def is_locked(self):
		"""
		Returns True if the user is locked (i.e. it doesn't have a password),
		False otherwise.
		"""
		
		status = True
		with open("/etc/shadow", "r") as f:
			for line in f:
				splt = line.split(":")
				if splt[0] == self.user:
					status = (splt[1] == "!")
					break
		
		splt = None
		return status

	def verify_password(self, oldpassword):
		"""
		Returns True if the password is verified, False otherwise.
		"""
		
		status = False
		with open("/etc/shadow", "r") as f:
			for line in f:
				splt = line.split(":")
				if splt[0] == self.user:
					status = pwd_context.verify(oldpassword, splt[1])
					break
		
		splt = None
		return status
	
	def change_password(self, newpassword):
		"""
		Changes the password.
		"""
		
		with open("/etc/shadow", "r") as f:
			lines = f.readlines()
		
		with open("/etc/shadow", "w") as f:
			for line in lines:
				splt = line.split(":")
				if splt[0] == self.user:
					# Change
					splt[1] = pwd_context.encrypt(newpassword, scheme=default_encryption)
				
				f.write(":".join(splt))
	
	def __init__(self, service, bus_name, passwd_entry):
		"""
		Initializes the object.
		"""
		
		self.service = service
		
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
		
		# Ensure the actual user can write its own properties without authenticating
		self.set_privileges = [0, self.uid]
		
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

