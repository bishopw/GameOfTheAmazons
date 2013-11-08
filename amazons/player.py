#!/usr/bin/env python

from board import WHITE, BLACK
from invalid_move_error import InvalidMoveError
from move import Move
from socket import *

class ResignGame(Exception):
	def __init__(self):
		pass
	
class QuitGame(Exception):
	def __init__(self):
		pass

class Player(object):
	def __init__(self, color, text_ui=False):
		self.color = color
		self.text_ui = text_ui
		
	@property
	def str_color(self):
		if self.color == WHITE:
			return "white"
		return "black"
		
	def __str__(self):
		return "Local Human"

	def next_move(self, game):
		if self.text_ui:
			return self.next_move_txt(game)
		return self.next_move_gui(game)

	def next_move_txt(self, game):
		ex = str(game.board.get_valid_moves()[0]).replace(',', '')
		print str(self) + ", please enter a move, e.g. '" + ex + "',"
		print "or enter 'r' to resign, or 'q' to quit."
		print ''
		i = raw_input('> ').strip().lower()
		print ''
		if i in ['q', 'quit']:
			raise QuitGame
		elif i in ['r', 'resign']:
			raise ResignGame
		try:
			return Move(i)
		except InvalidMoveError, e:
			print "Sorry, that doesn't seem to be a valid move."
			print str(e) + '.'
			print ''
			return self.next_move_txt(self, game)

	def next_move_gui(self, game):
		raise Exception("not implemented")


class NetworkPlayer(Player):
	def __init__(self, color, text_ui=False, **kwargs):
		super(NetworkPlayer, self).__init__(color, text_ui)
		if 'server' in kwargs:
			self.server = kwargs['server']
		else:
			self.server = 'localhost'
		if 'port' in kwargs:
			self.port = kwargs['port']
		else:
			self.port = 60987
		self.sock = socket(AF_INET, SOCK_DGRAM)
		self.sock.connect((self.server, self.port))
		self.sock.send("NEW_GAME:%s:%s" % (self.server, self.port))
		dat = self.sock.recv(1024)
		if not dat == "ACK:NEW_GAME":
			raise Exception("Could not connect to remote player")
		self.sock.close()
		
	def __str__(self):
		return "Network player"
	
	def next_move(self, game):
		self.sock = socket(AF_INET, SOCK_STREAM)
		self.sock.connect((self.server, self.port))
		self.sock.send("NEXT_MOVE")
		move = self.sock.recv(4096)
		print "Network player moves: %s" % move
		return Move(move)
	
class GameHostPlayer(Player):
	def __init__(self, color, text_ui=False, **kwargs):
		if 'port' in kwargs:
			self.port = kwargs['port']
		else:
			self.port = 60987
		self.sock = socket(AF_INET, SOCK_DGRAM)
		self.sock.connect(('localhost',self.port))
		dat = self.sock.recv(1024)
		self.sock.close()
		if dat.startswith("NEW_GAME"):
			_,self.opponent_host,self.opponent_port = dat.split(":")
			sock = socket(AF_INET, SOCK_DGRAM)
			sock.connect((self.opponent_host, self.opponent_port))
			self.sock.send("ACK:NEW_GAME")
		else:
			raise Exception("Got bad message: %s" % dat)
		super(GameHostPlayer, self).__init__(color)
	
	def send_my_move(self, move):
		sock = socket(AF_INET, SOCK_DGRAM)
		sock.connet((self.opponent_host, self.opponent_port))
		dat = sock.recv(1024)
		if dat == "NEXT_MOVE":
			sock.send(move)
		sock.close()
		
