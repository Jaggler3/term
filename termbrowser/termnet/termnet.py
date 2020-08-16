from http.server import BaseHTTPRequestHandler, HTTPServer
import time
from urllib.parse import unquote

hostName = "localhost"
serverPort = 8080

searchResult = """
text:[TITLE]
end
text:[URL]
end
cont
	-height: 2
end
"""

searchPage = """@termtype:m100
cont
	-padding: 5
	text:You searched for '[QUERY]'
	end
	cont
		-height: 3
	end
	[RESULTS]
end
"""

def search(query: str):
	return [{"title": "Page Title", "url": "http://www.www.www/www.term"}, {"title": "Page Title", "url": "http://www.www.www/www.term"}, {"title": "Page Title", "url": "http://www.www.www/www.term"}]

def respond(path: str):
	query = unquote(path[len("/search?q="):])
	results = search(query)
	resultsString = ""
	for r in results:
		resultsString += searchResult.replace("[TITLE]", r["title"]).replace("[URL]", r["url"])
	return searchPage.replace("[QUERY]", query).replace("[RESULTS]", resultsString)

class MyServer(BaseHTTPRequestHandler):
	def do_GET(self):
		if self.path.startswith("/search?q="):
			self.send_response(200)
			self.send_header("Content-type", "text/html")
			self.end_headers()
			self.wfile.write(bytes(respond(self.path), "utf-8"))
		else:
			self.send_response(200)
			self.send_header("Content-type", "text/html")
			self.end_headers()
			file = open("search.term")
			self.wfile.write(bytes(file.read(), "utf-8"))
			file.close()

if __name__ == "__main__":
	webServer = HTTPServer((hostName, serverPort), MyServer)
	print("Server started http://%s:%s" % (hostName, serverPort))

	try:
		webServer.serve_forever()
	except KeyboardInterrupt:
		pass

	webServer.server_close()
	print("Server stopped.")