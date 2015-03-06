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

from gi.repository import Gtk, GObject

import quickstart

class UI:
	
	"""
	The usersd user interface
	"""
	
	events = {
	
	}
	
	map_to = None
	error_message = None
	error_revealer = None
	
	def __getattr__(self, key):
		"""
		Proxy to the internal change_password_dialog.
		"""
		
		if self.map_to:
			return getattr(self.objects[self.map_to], key)
		else:
			# If we are here we don't have any other attributes to return
			raise AttributeError("UI object has no attribute '%s'" % key)
	
	def show_error(self, message):
		"""
		Shows an error message.
		"""
		
		if self.error_message:
			self.objects[self.error_message].set_text(message)
		if self.error_revealer:
			GObject.idle_add(self.objects[self.error_revealer].set_reveal_child, True)
	
	def hide_error(self):
		"""
		Hides the error message.
		"""
		
		if self.error_revealer:
			GObject.idle_add(self.objects[self.error_revealer].set_reveal_child, False)
	
	def __init__(self):
		"""
		Initializes the class.
		"""
		
		quickstart.events.connect(self)

@quickstart.builder.from_file("./usersd/usersd.glade")
class ChangePasswordDialog(UI):
	
	map_to = "change_password_dialog"
	error_message = "error_message"
	error_revealer = "error_revealer"
	
	def __init__(self, locked=False):
		"""
		Initializes the class.
		"""
		
		super().__init__()

		self.locked = locked
		
		# Add buttons
		self.objects.change_password_dialog.add_buttons(
			"Cancel",
			Gtk.ResponseType.CANCEL,
			"Change",
			Gtk.ResponseType.OK
		)
		self.objects.change_password_dialog.set_default_response(Gtk.ResponseType.OK)
		
		# Remove 'Old password' requirement if locked
		if self.locked:
			self.objects.old_password_label.hide()
			self.objects.old_password.hide()

@quickstart.builder.from_file("./usersd/usersd.glade")
class AddUserDialog(UI):
	
	map_to = "add_user_dialog"
	error_message = "add_error_message"
	error_revealer = "add_error_revealer"
	
	def __init__(self):
		"""
		Initializes the class.
		"""
		
		super().__init__()
		
		# Add buttons
		self.objects.add_user_dialog.add_buttons(
			"Cancel",
			Gtk.ResponseType.CANCEL,
			"Add",
			Gtk.ResponseType.OK
		)
		self.objects.add_user_dialog.set_default_response(Gtk.ResponseType.OK)
