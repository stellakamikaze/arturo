"""Il server HTTP finto dei banchi, senza socket.getfqdn all'avvio (#6454, 23/11/2026).

http.server.HTTPServer.server_bind chiede il nome completo dell'indirizzo. Sul runner macOS di GitHub
getfqdn("127.0.0.1") dura 35 secondi: ogni banco con un server finto aspettava 35 secondi prima del primo caso.
Il nome serve solo ai CGI, che i banchi non usano. Lo stesso server sta in bin/arturo_web.py (ServerLocale).
"""
import http.server
import socketserver


class ServerLocale(http.server.ThreadingHTTPServer):
    def server_bind(self) -> None:
        socketserver.TCPServer.server_bind(self)
        self.server_name, self.server_port = str(self.server_address[0]), self.server_address[1]
