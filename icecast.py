import xml.dom
import xml.dom.minidom
import shutil
import os.path
import subprocess

import zope.interface
from letsencrypt import interfaces
from letsencrypt.plugins import common

class IcecastInstaller(common.Plugin):
	zope.interface.implements(interfaces.IInstaller)
	zope.interface.classProvides(interfaces.IPluginFactory)

	description = "Installer plugin for Icecast2."

	@classmethod
	def add_parser_arguments(cls, add):
		#TODO: Can we automatically choose good defaults like /etc/icecast/icecast.xml ?
		add("configuration_file", help="The Icecast configuration file. E.g. /path/to/icecast.xml.")
		add("cert_and_key_file", default="icecast_cert_key.pem", help="The location of the file that contains the public and private key Icecast uses. This file is created by this plugin.")
		add("create_ssl_socket", choices=["true", "false"], default="true", help="If no ssl enabled socket exists should a new ssl enabled socket be created? If false the first socket found will be changed to use ssl. If no socket is defined a new ssl enabled socket will be created anyway.")
		add("new_ssl_socket_port", type=int, default=8443, help="Port of the newly created ssl enabled socket.")
	def __init__(self, *args, **kwargs):
		super(IcecastInstaller, self).__init__(*args, **kwargs)


		self.config_file = None
		#Check the following locations in order and see if they exist. Use the first one as the config file.
		self.common_config_locations = ['/etc/icecast2/icecast.xml',
					        '/etc/icecast/icecast.xml',
					        '/etc/icecast.xml',
                                                '/usr/local/etc/icecast.xml']
		self.concatened_cert_and_key_file = "icecast_cert_key.pem"
		self.create_ssl_socket = True
		self.default_ssl_port = 8443
	def prepare(self):
		self.config_file = self.conf("configuration_file")
		if self.config_file is not None and not os.path.isfile(self.config_file):
			raise RuntimeError('User supplied icecast configuration file does not exist.')
		self.concatenated_cert_and_key_file = self.conf("cert_and_key_file")
		self.create_ssl_socket = self.conf("create_ssl_socket") == "true"
		self.default_ssl_port = self.conf("new_ssl_socket_port")
		if self.config_file is None: #User did not supply a config file
			for path in self.common_config_locations:
				if os.path.isfile(path):
					self.config_file = path
			#No config file found
			raise RuntimeError('User did not supply an icecast configuration and file and the location could not be guessed.')
			#TODO: Check if icecast is running and get config file out of there with "ps" example: icecast2  2174  0.2  0.1  19196  5572 ?        Sl   Jun03  19:12 /usr/bin/icecast2 -b -c /etc/icecast2/icecast.xml
			#I dont like using ps or /proc because it is hard to know if they will work correctly or are available. Could use https://github.com/giampaolo/psutil if external dependency is ok?
		(self.config_document, self.config_root_node) = self.open_icecast_configuration(self.config_file)
	def more_info(self):
		return "Automatically enables SSL in Icecast. Sets the ssl-certificate option and creates an ssl enabled socket."
	def get_all_names(self):
		return [self.get_icecast_hostname()]
	def deploy_cert(self, domain, cert, key, cert_chain=None):
		#TODO: handle cert_chain
		def concatenate_cert_and_key(cert, key, out):
			"""Concatenate the public and private key into a single file because Icecast uses that format."""
			#Where to store it?
			#Which permissions to use? Let user manually handle permissions?
			with open(out, 'wb') as out_file:
				with open(cert, 'rb') as cert_file:
					shutil.copyfileobj(cert_file, out_file)
				with open(key, 'rb') as key_file:
					shutil.copyfileobj(key_file, out_file)
			return out
		file_path = concatenate_cert_and_key(cert, key, self.concatened_cert_and_key_file)
		#TODO: convert to absolute path
		self.set_icecast_ssl_certificate(file_path)
		if not self.exists_icecast_ssl_socket():
			if self.create_ssl_socket:
				self.make_icecast_ssl_socket()
			else:
				self.make_icecast_ssl_socket(self.find_first_socket_node())
	def enhance(self, domain, enhancement, options=None):
		#There is nothing to enhance
		pass
	def supported_enhancements(self):
		#We dont support any enhancements
		return []
	def get_all_certs_keys(self):
		#Return nothing because we use the concatenated file
		return []
	def save(self, title=None, temporary=False):
		self.write_to_file(self.config_file)
	def rollback_checkpoints(self, rollback=1):
		#TODO
		pass
	def view_config_changes(self):
		#TODO
		pass
	def config_test(self):
		#How to test? Is there even anything to test? We should never emit invalid xml.
		pass
	def restart(self):
		def is_pid_1_systemd():
			try:
				cmdline = open('/proc/1/cmdline', 'rb').read(7)
				return cmdline.startswith('systemd')
			except IOError:
				return false
		def execute_command(command):
			try:
				proc = subprocess.Popen(command)
				proc.wait()

				if proc.returncode != 0:
					print "Icecast restart command returned error."

			except (OSError, ValueError) as e:
				print "Failed to execute the restart icecast command."

		if is_pid_1_systemd():
			unit_script_locations = ['/usr/lib/systemd/system/',
                                                 '/etc/systemd/system/']
			icecast_service_names = ['icecast2.service, icecast.service']
			for path in unit_script_locations:
				for name in icecast_service_names:
					full_path = os.path.join(path, name)
					if os.path.isfile(full_path):
						execute_command(['systemctl', 'restart', name])
						return
			print("Found systemd but not the icecast service so it could not be restarted.")
		else:
			init_script_names = ['icecast2',
			                     'icecast']
			for path in init_script_names:
				if os.path.isfile(os.path.join('/etc/init.d/', path)):
					execute_command(['service', path, 'restart'])
					return
			print "Did not find the icecast service"
	def open_icecast_configuration( self, file ):
		document = xml.dom.minidom.parse( file )
		rootNode = document.documentElement
		return (document, rootNode)
	def get_element_node_by_name(self, parentNode, name):
		"""Looks for an Element Node in the chlild Nodes of parentNode and returns it if it exists or None otherwise."""
		childNodes = parentNode.childNodes
		index = 0
		for node in childNodes:
			if node.nodeType == xml.dom.Node.ELEMENT_NODE:
				if node.tagName == name:
					return childNodes[index]
			index += 1
		return None #No such node exists
	def follow_path(self, parentNode, path):
		"""Follows a path of Element Nodes starting from parentNode and following nodes specified in path. Returns the final node."""
		node = parentNode
		for name in path:
			node = self.get_element_node_by_name( node, name )
			if node is None:
				raise ValueError('Path does not exist.', path)
		return node
	def get_icecast_hostname(self):
		"""Returns the hostname specified in the icecast configuration."""
		hostnameNode = self.follow_path(self.config_root_node, ["hostname"])
		return hostnameNode.childNodes[0].data
	def exists_icecast_ssl_socket(self):
		"""Looks for an ssl enabled socket in the icecast configuration."""
		for node in self.config_root_node.childNodes:	
			if node.nodeType == xml.dom.Node.ELEMENT_NODE:
				if node.tagName == "listen-socket":
					ssl_node = self.get_element_node_by_name(node, "ssl")
					if ssl_node is not None:
						if ssl_node.childNodes[0].data == "1":
							return True
		return False
	def find_first_socket_node(self):
		"""Returns the first socket xml node in the icecast configuration. If none are found returns None."""
		return self.get_element_node_by_name(self.config_root_node, "listen-socket")
	def make_icecast_ssl_socket(self, socket_node=None):
		"""Creates an ssl enabled socket in the icecast configuration.
                   If socket_node is specified ssl will be enabled for that socket. If not a new socket will be created."""
		document = self.config_document
		if socket_node is None:
			comment = document.createComment("ssl socket inserted by lets encrypt")
			new_node = document.createElement("listen-socket")
			port_node = document.createElement("port")
			port_node.appendChild(document.createTextNode(str(self.default_ssl_port)))
			ssl_node = document.createElement("ssl")
			ssl_node.appendChild(document.createTextNode("1"))
			new_node.appendChild(document.createTextNode("\n        "))
			new_node.appendChild(port_node)
			new_node.appendChild(document.createTextNode("\n        "))
			new_node.appendChild(ssl_node)
			new_node.appendChild(document.createTextNode("\n    "))
			self.config_root_node.appendChild(document.createTextNode("    "))
			self.config_root_node.appendChild(comment)
			self.config_root_node.appendChild(document.createTextNode("\n    "))
			self.config_root_node.appendChild(new_node)	
			self.config_root_node.appendChild(document.createTextNode("\n    "))
		else:
			ssl_node = self.get_element_node_by_name(socket_node, "ssl")
			if ssl_node is None:
				new_ssl_node = document.createElement("ssl")
	                        new_ssl_node.appendChild(document.createTextNode("1"))
				socket_node.appendChild(new_ssl_node)
				socket_node.appendChild(document.createTextNode("\n    "))
			else:
				ssl_node.childNodes[0].data = "1"
	def set_icecast_ssl_certificate(self, path_to_certificate):
		"""Sets the ssl certificate in the icecast configuration.
		   If the ssl-certificate is already set it will be changed to the new one. If not the node will be created."""
		document = self.config_document
		currentNode = self.config_root_node

		currentNode = self.follow_path(currentNode, ["paths"])

		certificate_node = self.get_element_node_by_name(currentNode, "ssl-certificate")

		if certificate_node is not None:
			certificate_node.childNodes[0].data = path_to_certificate
		else:
			comment = document.createComment('ssl-certificate inserted by lets encrypt')
			certificate_node = document.createElement('ssl-certificate')
			text_node = document.createTextNode(path_to_certificate)
			certificate_node.appendChild(text_node)
			currentNode.appendChild(document.createTextNode("    "))
			currentNode.appendChild(comment)
			currentNode.appendChild(document.createTextNode("\n        "))
			currentNode.appendChild(certificate_node)
			currentNode.appendChild(document.createTextNode("\n    "))
			
	def write_to_file(self, path):
		"""Write the current in memory configuration to a file."""
		with open(path, 'w') as f:
			self.config_document.writexml(f)
