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

import quickstart

@quickstart.builder.from_file("./usersd/usersd.glade")
class ChangePasswordDialog:
	
	"""
	The ChangePasswordDialog is the dialog that the user will get when
	trying to change password.
	
	We do not require clients to send us the (hashed) passwords as they may
	be sniffed with a simple dbus monitor.
	
	Using this method, the passwords will remain in this application, and aren't
	sent anywhere.
	"""
	
	events = {
		"clicked" : ("close_button", "continue_button"),
	}
	
	def show(self, user):
		"""
		Shows the dialog.
		"""
		
		self.objects.main.present()
	
	def clear_and_hide(self):
		"""
		Clears entries and hides things.
		"""

		self.objects.main.destroy()
	
	def on_close_button_clicked(self, button):
		"""
		Fired when the Close button has been clicked.
		"""
		
		self.clear_and_hide()
	
	def on_continue_button_clicked(self, button):
		"""
		Fired when the Continue button has been clicked.
		"""
		
		self.clear_and_hide()
	
	def __init__(self):
		"""
		Initialization.
		"""
		
		quickstart.events.connect(self)
		
