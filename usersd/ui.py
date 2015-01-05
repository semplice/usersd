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

@quickstart.builder.from_file("./usersd/usersd.glade")
class ChangePasswordDialog:
	
	"""
	The usersd user interface
	"""
	
	events = {
	
	}
	
	def __getattr__(self, key):
		"""
		Proxy to the internal change_password_dialog.
		"""
		
		return getattr(self.objects.change_password_dialog, key)
	
	def show_error(self, message):
		"""
		Shows an error message.
		"""
		
		self.objects.error_message.set_text(message)
		GObject.idle_add(self.objects.error_revealer.set_reveal_child, True)
	
	def hide_error(self):
		"""
		Hides the error message.
		"""
		
		GObject.idle_add(self.objects.error_revealer.set_reveal_child, False)
	
	def __init__(self, locked=False):
		"""
		Initializes the class.
		"""
		
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
		
		quickstart.events.connect(self)
