#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# usersd - user management daemon
# Copyright (C) 2014-2015  Eugenio "g7" Paolantonio
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
from distutils.core import setup, Command
from distutils.command.build import build
from distutils.command.install import install

import subprocess
import shutil

l10n_path = "./po"

APP_NAME = "usersd"

class CreatePotTemplate(Command):
	"""
	Creates a .pot template.
	"""
	
	description = "creates a .pot localization template from the program sources."
	user_options = []
	
	def initialize_options(self):
		"""
		Initialize options
		"""
		
		self.cwd = None
	
	def finalize_options(self):
		"""
		Finalize options
		"""
		
		self.cwd = os.getcwd()
	
	def run(self):
		"""
		Does things.
		"""
		
		assert os.getcwd() == self.cwd, "You must be in the package root: %s" % self.cwd
		
		output_file = os.path.join(self.cwd, l10n_path, APP_NAME, "%s.pot" % APP_NAME)
		
		# Blank-out the output file
		with open(output_file, "w") as f:
			f.write("")
		
		py_files = []
		glade_files = []
		
		for directory, dirnames, filenames in os.walk("."):
			for file_ in filenames:
				if file_.endswith(".py"):
					py_files.append(os.path.join(directory, file_))
				elif file_.endswith(".glade"):
					glade_files.append(os.path.join(directory, file_))
					
		subprocess.call([
			"xgettext",
			"--language=Python",
			"--from-code=utf-8",
			"--keyword=_",
			"--output=%s" % output_file,
		] + py_files)
		
		for file_ in glade_files:
			subprocess.call([
				"intltool-extract",
				"--type=gettext/glade",
				file_
			])
			subprocess.call([
				"xgettext",
				"--from-code=utf-8",
				"--language=C",
				"--keyword=N_",
				"-j",
				"--output=%s" % output_file,
				"-j",
				file_ + ".h"
			])
			os.remove(file_ + ".h")

class CustomBuild(build):
	"""
	Hooks.
	"""
	
	def run(self):
		"""
		Runs the installation.
		"""
		
		super().run()
		
		# Build mos
		for directory, dirnames, filenames in os.walk(l10n_path):
			for file_ in filenames:
				if file_.endswith(".po"):
					source = os.path.join(directory, file_)
					target_dir = os.path.join("./build", directory)
					target = os.path.join(target_dir, file_.replace(".po",".mo"))
					
					if not os.path.exists(target_dir):
						os.makedirs(target_dir)
					
					print("Compiling translation %s" % file_)
					subprocess.call(["msgfmt", "--output-file=%s" % target, source])

class CustomInstall(install):
	"""
	Hooks.
	"""
	
	def run(self):
		"""
		Runs the installation.
		"""
		
		super().run()
		
		# Install mos
		for directory, dirnames, filenames in os.walk(os.path.join("./build", l10n_path)):
			for file_ in filenames:
				if file_.endswith(".mo"):
					source = os.path.join(directory, file_)
					target_dir = os.path.join(
						self.root if self.root else "/",
						"usr/share/locale",
						file_.replace(".mo",""),
						"LC_MESSAGES"
					)
					target = os.path.join(target_dir, os.path.basename(directory) + ".mo")
					
					if not os.path.exists(target_dir):
						os.makedirs(target_dir)
					
					shutil.copyfile(source, target)
					os.chmod(target, 644)

setup(
	cmdclass={
		"pot": CreatePotTemplate,
		"build": CustomBuild,
		"install": CustomInstall
	},
	name=APP_NAME,
	version='0.90.2',
	description='User management daemon.',
	author='Eugenio Paolantonio',
	author_email='me@medesimo.eu',
	url='https://github.com/semplice/usersd',
	scripts=['usersd-service.py'],
	packages=[
		'usersd'
	],
	data_files=[
		("/usr/share/usersd/usersd", ["usersd/usersd.glade"]),
		("/etc/dbus-1/system.d", ["data/org.semplicelinux.usersd.conf"]),
		("/usr/share/polkit-1/actions", ["data/org.semplicelinux.usersd.policy"]),
		("/usr/share/dbus-1/system-services", ["data/org.semplicelinux.usersd.service"])
	],
	requires=[
		'os',
		'gi.repository.Gtk',
		'gi.repository.Gio',
		'gi.repository.GObject',
		'gi.repository.GLib',
		'gi.repository.Polkit',
		'passlib',
		'quickstart',
		'collections.OrderedDict',
		'subprocess'
	],
)
