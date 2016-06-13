import argparse
import errno
import os
import os.path
import SimpleHTTPServer
import SocketServer
import socket

import markdown
import pygments.formatters


def parse_args():
	desc = 'Serve Markdown files from current directory'
	parser = argparse.ArgumentParser(description=desc)
	parser.add_argument('-n','--name', default='localhost', help='listen host name (default: %(default)s)')
	parser.add_argument('-p','--port', type=int, default=8000, help='listen TCP port (default: next available from %(default)s)')
	return parser.parse_args()

class MarkdownHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
	extensions_map = SimpleHTTPServer.SimpleHTTPRequestHandler.extensions_map
	extensions_map['.md'] = 'text/html'

	def do_GET(self):
		basename = os.path.basename(self.path)
		if not basename.endswith('.md'):
			SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)
		else:
			fh = self.send_head()
			for s in self.server.stylesheets:
				self.wfile.write(r'<link rel="stylesheet" href="{}" type="text/css" />'.format(s))
			markdown.markdownFromFile(
				os.path.join('.', self.path[1:]),
				self.wfile,
				extensions=['codehilite', 'toc(title=Table of Contents)'])
			fh.close()

class MarkdownServer(SocketServer.TCPServer):
	def __init__(self, *args, **opts):
		SocketServer.TCPServer.__init__(self, *args)
		self.stylesheets = opts['stylesheets']

	def shutdown(self):
		for s in self.stylesheets:
			print 'deleting stylesheet file "{}"'.format(s)
			os.unlink(s)
		SocketServer.TCPServer.shutdown(self)

def generate_codehilite_stylesheet(out_fname):
	stylesheet = pygments.formatters.HtmlFormatter().get_style_defs('.codehilite')
	print 'generating codehilite stylesheet file "{}"'.format(out_fname)
	fh = open(out_fname, 'w')
	fh.write(stylesheet)
	fh.close()

def main(args):
	codehilite_stylesheet_file = 'hilite.css'
	generate_codehilite_stylesheet(codehilite_stylesheet_file)

	svr_options = {
		'stylesheets': [codehilite_stylesheet_file]
	}

	port = args.port
	while port < 2**16:
		try:
			httpd = MarkdownServer((args.name, port), MarkdownHandler, **svr_options)
			print 'serving on {}:{}...'.format(args.name, port)
			httpd.serve_forever()
		except socket.error as e:
			if e.errno == errno.EADDRINUSE:
				port += 1
		except KeyboardInterrupt:
			print 'shutting down...'
			httpd.shutdown()
			break

if __name__ == '__main__':
	main(parse_args())
