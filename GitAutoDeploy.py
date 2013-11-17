#!/usr/bin/env python

import json, urlparse, sys, os
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import subprocess

class GitAutoDeploy(BaseHTTPRequestHandler):

	CONFIG_FILEPATH = './GitAutoDeploy.conf.json'
	config = None
	quiet = False
	daemon = False

	@classmethod
	def getConfig(myClass):
		if(myClass.config == None):
			try:
				configString = open(myClass.CONFIG_FILEPATH).read()
			except:
				sys.exit('Could not load ' + myClass.CONFIG_FILEPATH + ' file')

			try:
				myClass.config = json.loads(configString)
			except:
				sys.exit(myClass.CONFIG_FILEPATH + ' file is not valid json')

			for repository in myClass.config['repositories']:
				if(not os.path.isdir(repository['path'])):
					sys.exit('Directory ' + repository['path'] + ' not found')
				if(not os.path.isdir(repository['path'] + '/.git')):
					sys.exit('Directory ' + repository['path'] + ' is not a Git repository')

		return myClass.config

	def do_POST(self):
		responses = self.parseRequest()
		for response in responses:
			url = response['repository']['url']
			paths = self.getMatchingPaths(url)
			for path in paths:
				git_pull_output = self.pull(path)
				deploy_output = self.deploy(path)
				if self.is_gmail_enabled():
					self.send_gmail(response, path, git_pull_output, deploy_output)

		self.respond()

	def parseRequest(self):
		length = int(self.headers.getheader('content-length'))
		body = self.rfile.read(length)
		post = urlparse.parse_qs(body)
		items = []

		# If payload is missing, we assume gitlab syntax.
		if not 'payload' in post:
			response = json.loads(body)
			if 'repository' in body:
				items.append(response)

		# Otherwise, we assume github syntax.
		else:
			for itemString in post['payload']:
				item = json.loads(itemString)
				items.append(item)

		return items

	def getMatchingPaths(self, repoUrl):
		res = []
		config = self.getConfig()
		for repository in config['repositories']:
			if(repository['url'] == repoUrl):
				res.append(repository['path'])
		return res

	def respond(self):
		message = 'OK'
		self.send_response(200)
		self.send_header("Content-type", "text")
		self.send_header("Content-length", str(len(message)))
		self.end_headers()
		self.wfile.write(message)

	def pull(self, path):
		if(not self.quiet):
			print "\nPost push request received"
			print 'Updating ' + path
		# running process STDERR redirected to STDOUT
		p = subprocess.Popen(['cd "' + path + '" && git pull'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
		out, err = p.communicate()
		return out

	def deploy(self, path):
		config = self.getConfig()
		for repository in config['repositories']:
			if(repository['path'] == path):
				if 'deploy' in repository:
					if(not self.quiet):
						print 'Executing deploy command'
					p = subprocess.Popen(['cd "' + path + '" && ' + repository['deploy']], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
					out, err = p.communicate()
					return out
				break
		return "" # empty - if no deploy script - so no output either

	def is_gmail_enabled(self):
		return 'gmail' in self.getConfig().keys()

	def send_gmail(self, response, path, git_pull_output, deploy_output):
		import smtplib
		import socket

		config = self.getConfig()
		gmail_config = config['gmail']

		url = response['repository']['url']
		commits = response['commits']
		push_user = response['user_name']
		repo_name = response['repository']['name']

		message  = "From: %s\n" % gmail_config['username']
		message += "To: %s\n" % (", ".join(gmail_config['recipients']))
		message += "Content-Type: text/plain; charset=utf-8\n"
		message += "Subject: Gitlab deploy (%s -> %s)\n\n" % (push_user, repo_name) # note: double line break
		message += "Deploying: %s -> %s\n\n" % (url, path)

		for commit in commits:
			message += "%s\n" % commit['url']
			message += "%s (%s):\n" % (commit['author']['name'], commit['timestamp'])
			message += "%s\n\n" % commit['message'] # double line-end

		message += git_pull_output + "\n\n"
		message += deploy_output

		try:
			server = smtplib.SMTP('smtp.gmail.com:587')
			server.ehlo()
			server.starttls()
			server.login(gmail_config['username'], gmail_config['password'])
			server.sendmail(gmail_config['username'], gmail_config['recipients'], message.encode('utf-8'))
			server.close()
			if (not self.quiet):
				print 'successfully sent the mail'
		except socket.error as e:
			print "socket error - firewall?"
		except:
		    print "failed to send mail"

def main():
	try:
		server = None
		for arg in sys.argv:
			if(arg == '-d' or arg == '--daemon-mode'):
				GitAutoDeploy.daemon = True
				GitAutoDeploy.quiet = True
			if(arg == '-q' or arg == '--quiet'):
				GitAutoDeploy.quiet = True

		if(GitAutoDeploy.daemon):
			pid = os.fork()
			if(pid != 0):
				sys.exit()
			os.setsid()

		if(not GitAutoDeploy.quiet):
			print 'Github & Gitlab Autodeploy Service v 0.1 started'
		else:
			print 'Github & Gitlab Autodeploy Service v 0.1 started in daemon mode'

		server = HTTPServer(('', GitAutoDeploy.getConfig()['port']), GitAutoDeploy)
		server.serve_forever()
	except (KeyboardInterrupt, SystemExit) as e:
		if(e): # wtf, why is this creating a new line?
			print >> sys.stderr, e

		if(not server is None):
			server.socket.close()

		if(not GitAutoDeploy.quiet):
			print 'Goodbye'

if __name__ == '__main__':
	 main()
