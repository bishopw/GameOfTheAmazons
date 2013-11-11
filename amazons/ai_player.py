#!/usr/bin/env python

from multiprocessing import Pool, TimeoutError, freeze_support, current_process
from random import randint
from time import sleep, time
from gc import collect

from player import Player
from board import Board
from move import Move
from square import Square
from squares import Squares

# from memory_profiler import profile

WHITE = 1
BLACK = -1

def evaluate(board):
    """
    Returns a normalized board evaluation score from 0.0 (worst) to 100.0 (best),
    or -inf (guaranteed loss), or +inf (guaranteed win) based on the weighted
    results of all board evaluation functions.
    Note that all evaluation scores are given from the perspective of WHITE.
    """
    if (board.to_move == 'white' and len(board.get_valid_moves()) == 0):
        return float("-inf")
    if (board.to_move == 'black' and len(board.get_valid_moves()) == 0):
        return float("inf")

    return (eval_mobility(board) * 1.0) / 1.0

def eval_mobility(board):
    """
    Returns mobility score for the given board, from 0.0 to 100.0.
    """
    move_count = len(board.get_valid_moves())
    opp_move_count = len(board.get_valid_opponent_moves())
    w_move_count = move_count
    b_move_count = opp_move_count
    if board.to_move == 'black':
        w_move_count = opp_move_count
        b_move_count = move_count
    if w_move_count == 0:
        return 0.0
    if b_move_count == 0:
        return 100.0
    relative_mobility = 50.0
    if w_move_count >= b_move_count:
        difference = (1.0 - (float(b_move_count) / float(w_move_count))) * 50.0
        relative_mobility += difference
    else:
        difference = (1.0 - (float(w_move_count) / float(b_move_count))) * 50.0
        relative_mobility -= difference
    return relative_mobility

def is_terminal(board):
    return len(board.get_valid_moves()) == 0

def negamax(board, depth, alpha, beta, color, nodes_evaluated):
    """
    Returns the best possible future board evaluation score for the specified
    node, given the specified search depth.
    Based on negamax algorithm from http://en.wikipedia.org/wiki/Negamax
    """
    if depth == 0 or is_terminal(board):
        nodes_evaluated[0] = nodes_evaluated[0] + 1
        return float(color) * evaluate(board)
    best_value = float("-inf")
    moves = list(board.get_valid_moves())
    for move in moves:
        board.move_in_place(move)
        val = -1.0 * negamax(board, depth - 1, -beta, -alpha, -color)
        board.undo_move_in_place(move)
        best_value = max(best_value, val)
        alpha = max(alpha, val)
        if alpha >= beta:
            break
    return best_value

#@profile
def decide(input_list):
    """
    Main function for a thinker process to run.
    Evaluate a chunk of moves from the given moves list to the given depth,
    starting at starting_index.
    """
    board = input_list[0]
    moves = input_list[1]
    move_count = len(moves)
    starting_index = input_list[2]
    chunk_size = input_list[3]
    depth = input_list[4]
    abort_time = input_list[5]

    if (starting_index >= move_count):
        # print 'Process %s: Aborting: no work to do.' % current_process().name
        return None
    if (starting_index + chunk_size > move_count):
        chunk_size = move_count - starting_index

    # Decision statistics.
    total_time = 0
    nodes_evaluated = [0]

    start_time = time()
    best_value = float("-inf")
    best_move = 'resign'
    # print 'Process %s: Evaluating moves %d through %d...' % (current_process().name, starting_index, starting_index + chunk_size - 1)

    # Evaluate each root move at this depth.
    total_move_values = 0
    curr_best_value = (float("-inf") if board.to_move == 'white' 
                       else float("inf"))
    curr_best_move = 'resign'
    tm = board.to_move
    for i in range(starting_index, starting_index + chunk_size):
        move = moves[i]
        board.move_in_place(move)
        if abort_time != None and time() > abort_time:
            # print 'Process %s: Aborting: out of time.' % current_process().name
            board.undo_move_in_place(move)
            return None # Out of time.  Abort mission.
        val = None
        if tm == 'white':
            val = negamax(board, depth, float("-inf"), float("inf"), WHITE,
                nodes_evaluated)
            # Maximize highest possible evaluation.
            if (val > curr_best_value):
                curr_best_value = val
                curr_best_move = move
        else:
            val = (-1.0 *
                negamax(board, depth, float("-inf"), float("inf"), BLACK,
                    nodes_evaluated))
            # Minimize highest possible evaluation.
            if (val < curr_best_value):
                curr_best_value = val
                curr_best_move = move
        board.undo_move_in_place(move)
        total_move_values += val
        # print "Process %s: Move %d: %s: mobility score %f." % (current_process().name, i, str(move), val)
        # print "  curr_best_move: %s, curr_best_value: %f" % (str(curr_best_move), curr_best_value)

    curr_time = time()
    total_time = curr_time - start_time

    # print "Process %s: Best move was '%s' with value %f." % (current_process().name, str(curr_best_move), curr_best_value)
    # print '              time: ' + str(total_time) + ' sec'
    # print '   moves evaluated: ' + str(chunk_size)
    # print '    avg_move_value: ' + str(total_move_values / float(chunk_size))
    # print '  boards_evaluated: ' + str(nodes_evaluated[0])

    return {
        "best_move": curr_best_move,
        "best_move_value": curr_best_value,
        "time": total_time,
        "starting_index": starting_index,
        "moves_evaluated": chunk_size,
        "avg_move_value": total_move_values / float(chunk_size),
        "boards_evaluated": nodes_evaluated[0]
    }

# Spin up AI thinker process.
freeze_support() # Some weird compatibility thing having to do with installers.
PROCESS_COUNT = 3
pool = Pool(processes=PROCESS_COUNT)

class AIPlayer(Player):
    def __init__(self, color, **kwargs):
        super(AIPlayer, self).__init__(color)
        self.difficulty = 5
        if 'difficulty' in kwargs:
            self.difficulty = kwargs['difficulty']
        self.results = None
        self.results_to_collect = 0
        self.board = None
        
    def __str__(self):
        return "Computer AI"

    def launch_workers(self, depth):
        """
        Split the board evaluation task into PROCESS_COUNT chunks and delegate
        it to the worker processes.
        """
        sample_size_target = 4 + int((float(self.difficulty - 1) / 9.0) * 1600.0)
        all_moves = self.board.get_valid_moves()

        moves = all_moves
        if len(all_moves) > sample_size_target:
            moves = []
            sample_every = int(max(1, int(float(len(all_moves)) / float(sample_size_target)) + 1))
            i = 0
            for mv in all_moves:
                if i % sample_every == 0:
                    moves.append(mv)
                i += 1
        move_count = len(moves)
        chunk_size = int(move_count / PROCESS_COUNT) + 1
        abort_time = None
        input_tasks = [[self.board, moves, i * chunk_size, chunk_size, depth, abort_time]
            for i in range(PROCESS_COUNT)]
        self.output_tasks = []
        self.results_to_collect = PROCESS_COUNT
        # print ('Main Process: Launching ' + str(PROCESS_COUNT) +
        #     ' workers to process ' + str(move_count) + ' out of ' + str(len(all_moves)) + ' moves at depth ' +
        #     str(depth) + '.')
        self.results = pool.imap(decide, input_tasks)
        # self.sync_output = []
        # for task in input_tasks:
        #     self.sync_output.append(decide(task))

    def start_thinking(self, board, clock=None):
        """Start considering the next move for the specified game."""
        # Perform a deepening recursive search through the move tree until we
        # run out of time or hit our target depth.
        self.results = None
        self.results_to_collect = 0
        self.board = board
        self.target_depth = 0
        self.current_depth = 0
        self.last_completed_depth = -1
        self.target_time = None
        self.start_time = time()
        self.launch_workers(self.current_depth)

    def stop_thinking(self):
        """Stop considering moves, whether or not a move was decided."""
        pass

    def next_move(self):
        """
        Return the move decided on after the last call to start_thinking(),
        or return None if the next move is not decided yet.
        """
        if self.results == None:
           return self.results
        try:
            # Collect worker process results.
            while self.results_to_collect > 0:
                self.output_tasks.append(self.results.next(timeout=0.05))
                self.results_to_collect -= 1

            # self.output_tasks = self.sync_output

            # Are we really done, or should we try for a deeper ply?
            self.last_completed_depth = self.current_depth
            if (self.current_depth < self.target_depth):
                self.current_depth += 1
                self.launch_workers(self.current_depth)
                return None

            # TODO: if we ran out of time, return none.

            # OK we're really done.  Aggregate worker process results.
            total_time = time() - self.start_time
            best_move = 'resign'
            best_move_value = (float('-inf') if self.board.to_move == 'white'
                else float('inf'))
            total_boards_evaluated = 0
            total_avg_move_value = 0
            total_moves_evaluated = 0
            for output in self.output_tasks:
                if output == None:
                    # This was an aborted worker process - no work or 
                    # ran out of time.
                    continue
                if self.board.to_move == 'white':
                    if output['best_move_value'] > best_move_value:
                        best_move = output['best_move']
                        best_move_value = output['best_move_value']
                else:
                    if output['best_move_value'] < best_move_value:
                        best_move = output['best_move']
                        best_move_value = output['best_move_value']
                total_boards_evaluated += output['boards_evaluated']
                total_avg_move_value += (output['avg_move_value'] *
                    float(output['moves_evaluated']))
                total_moves_evaluated += output['moves_evaluated']
            total_avg_move_value /= float(total_moves_evaluated)

            # Resign if a win seems unlikely.
            if self.board.to_move == 'white':
                if best_move_value < 20.0:
                    best_move = 'resign'
            else:
                if best_move_value > 80.0:
                    best_move = 'resign'

            print self.board.to_move.capitalize() + ' moves ' + str(best_move) + '.'
            print '        move value: ' + str(best_move_value)
            print '    possible moves: ' + str(len(self.board.get_valid_moves()))
            print '   avg. move value: ' + str(total_avg_move_value)
            # print ('       target time: ' + str(self.target_time) +
            #     (' sec' if type(self.target_time) == int else ''))
            print '       actual time: ' + str(int(total_time)) + ' sec'
            # print '      target depth: ' + str(self.target_depth)
            # print '      actual depth: ' + str(self.last_completed_depth)
            print '  boards evaluated: ' + str(total_boards_evaluated)

            # Reset members.
            self.results = None
            self.results_to_collect = 0
            self.board = None
            self.output_tasks = []
            self.input_tasks = None

            return best_move

        except TimeoutError:
            return None
