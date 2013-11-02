#!/usr/bin/env python

from board import WHITE, BLACK
from invalid_move_error import InvalidMoveError
from move import Move
from random import randint
from socket import *
import pickle

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
	
	
class AIPlayer(Player):
	def __init__(self, color, **kwargs):
		super(AIPlayer, self).__init__(color)
		
	def __str__(self):
		return "Computer AI"

	def next_move(self, game):
		"""Temporary stand-in for AI opponent.  Pick a random valid move."""
		valid_moves = game.board.get_valid_moves()
		return valid_moves[randint(0, len(valid_moves) - 1)]

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
	
	def __str__(self):
		return "Network player"
	
	def next_move(self, game):
		sock = socket(AF_INET, SOCK_STREAM)
		sock.connect((self.server, self.port))
		sock.send("/".join([str(x) for x in game.board.get_valid_moves()]))
		move = sock.recv(4096)
		print "Network player moves: %s" % move
		return Move(move)