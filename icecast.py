import xml.dom
import xml.dom.minidom
import shutil

import zope.interface
from letsencrypt import interfaces
from letsencrypt.plugins import common


class IcecastInstaller(common.Plugin):
	zope.interface.implements(interfaces.IInstaller)
	zope.interface.classProvides(interfaces.IPluginFactory)

	description = "Installer plugin for Icecast2."

	config_file = "plugin_input.xml"
	concatened_cert_and_key_file = "icecast_cert_key.pem"
	create_ssl_socket = True
	default_ssl_port = 8443

	@classmethod
	def add_parser_arguments(cls, add):
		#TODO: Can we automatically choose good defaults like /etc/icecast/icecast.xml ?
		add("configuration_file", default="icecast.xml", help="The Icecast configuration file. E.g. /path/to/icecast.xml.")
		add("cert_and_key_file", default="icecast_cert_key.pem", help="The location of the file that contains the public and private key Icecast uses. This file is created by this plugin.")
		add("create_ssl_socket", choices=["true", "false"], default="true", help="If no ssl enabled socket exists should a new ssl enabled socket be created? If false the first socket found will be changed to use ssl. If no socket is defined a new ssl enabled socket will be created anyway.")
		add("new_ssl_socket_port", type=int, default=8443, help="Port of the newly created ssl enabled socket.")
	def prepare(self):
		self.config_file = self.conf("configuration_file")
		self.concatenated_cert_and_key_file = self.conf("cert_and_key_file")
		self.create_ssl_socket = self.conf("create_ssl_socket") == "true"
		self.default_ssl_port = self.conf("new_ssl_socket_port")
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
		print "save icecast"
		print "Saving. Title:", title, "temporary:", temporary
		self.write_to_file(self.config_file)
		#TODO use reverter
		pass
	def rollback_checkpoints(self, rollback=1):
		print "rollback icecast"
		#TODO
		pass
	def view_config_changes(self):
		print "view config changes icecast"
		#TODO
		pass
	def config_test(self):
		print "config test icecast"
		#How to test? Is there even anything to test? We should never emit invalid xml.
		pass
	def restart(self):
		print "restart icecast"
		#TODO: How to restart Icecast?
		pass


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
