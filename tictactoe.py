import numpy
from random import sample
from numpy import diag
import cPickle

class State(numpy.ndarray):
    symbols = {0: "_", 1: "X", 2: "O"}
    
    #3x3 array of zeros
    def __new__(subtype): 
        arr = numpy.zeros((3,3), dtype=numpy.int8)
        return arr.view(subtype)

    def __hash__(s): 
        flat = s.ravel() #array as vector
        code = 0
        for i in xrange(9): code += pow(3,i) * flat[i] #xrange(9) = seq(1,9) in R, pow(3,i) = 3^i
        return code

    def won(s, player): #all possibilities of winning
        x = s == player
        return numpy.hstack( (x.all(0), x.all(1), diag(x).all(), diag(x[:,::-1]).all()) ).any() #hstack = cbind in R

    def full(s):
        return (s != 0).all()

    def __str__(s): #fill the board with current state
        out = [""]
        for i in xrange(3):
            for j in xrange(3):
                out.append( s.symbols[ s[i,j] ] ) #we defined the possible symbols at the begining of the class
            out.append("\n")
        return str(" ").join(out)
        
        
class Learner:
    def __init__(s, player):
        s.valuefunc = dict()
        s.laststate_hash = None
        s.alpha = 0.9
        s.player = player
        s.gamehist = []
        s.traced = False
       
    def enum_actions(s, state):
        #enumerate all possible actions from given state
        res = list()
        for i in xrange(3):
            for j in xrange(3):
                #if a given position in the given state
                #is still empty then add it as a possible action 
                if state[i,j] == 0:
                    res.append( (i,j) )
        #return list of all possible actions
        return res

    def value(s, state, action):
        "Assumption: Game has not been won by other player"
        #modify the state: put to the given place(action) the given symbol(player)
        state[action] = s.player
        #hash value is an id used to compare disctionary keys quickly
        #id of new state
        hashval = hash(state)
        #access value of the new state
        val = s.valuefunc.get( hashval )
        #if new state has no value yet
        if val == None:
            #if new state is winning assign value 1
            if state.won(s.player): val = 1.0
            #if new state is final but player did not win assign value 0
            elif state.full(): val = 0.0
            #if none then assign 0.1??????
            else: val = 0.1
            #assign value to the new state
            s.valuefunc[hashval] = val
        #reset state to the old value (I guess we call "value" only for possible action, 
        #meaning we step only to empty positions)    
        state[action] = 0
        #return value of the new state
        return val
        
    def next_action(s, state):
        valuemap = list()
        #enumerate over all possible actions
        for action in s.enum_actions(state):
            #check value of the new state if you make a possible action
            val = s.value(state, action)
            #add it to value map associated with the given action
            valuemap.append( (val, action) )
        #Find the actions with the highest value
        valuemap.sort(key=lambda x:x[0], reverse=True)
        maxval = valuemap[0][0]
        valuemap = filter(lambda x: x[0] >= maxval, valuemap)
        #randomize over the max value actions and return one of them 
        return sample(valuemap,1)[0]

    def next(s, state):
        #If the other player won assign value -1
        if state.won(3-s.player):
            val = -1
        #If the game ended assign value 0.1
        elif state.full():
            val = -0.1
        else:
            #Otherwise find the best action with the associated value
            (val, action) = s.next_action(state)
            #Redefine state according to this action (put the given 
            #player`s sign to the optimal action)
            state[action] = s.player

        if state.won(1) or state.won(2) or state.full():
            #If game is finish change traced value to true
            s.traced = True
            
        #learning step
        #If there was a previous state
        if s.laststate_hash != None:
            #update the value of the previous state (meaning the state you were in the previous step) 
            #based on the original value of the previous state and the value of the new state
            s.valuefunc[s.laststate_hash] = (1.0-s.alpha) * s.valuefunc[s.laststate_hash] + s.alpha * val
        #update laststate value
        s.laststate_hash = hash(state)
        #append previous state to the game history
        s.gamehist.append(s.laststate_hash)
        
    def reset(s):
        #reset the class except valuefunction
        #basically start new game but keep values you already updated
        s.laststate_hash = None
        s.gamehist = []
        s.traced = False
                        
class Game:
    #description of the game = the variable 
    # what objects it should have inside
    def __init__(s):
        s.learner = Learner(player=2) #define if we want a second player 
        s.reset() #define that reset is part of the game 
        s.sp = Selfplay(s.learner) #if we want to play against myself
    
    #define the reset function    
    def reset(s):
        s.state = State() 
        s.learner.reset() 
        print "** New Game **"
        print s.state

    def __call__(s, pi,pj): 
        j = pi -1 #take the first coordinate of the previous state
        i = pj - 1 #take the second coordinate of the previous state
        if s.state[j,i] == 0:
            s.state[j,i] = 1
            s.learner.next(s.state)
        else:
            print "Invalid move"
        print s.state #,hash(s.state)

        if s.state.full() or s.state.won(1) or s.state.won(2):
            if s.state.won(1):
                print "You WIN"
            elif s.state.won(2):
                print "You LOOSE"
            else:
                print "DRAW Game"
            s.reset() #reset the game 

    def selfplay(s, n=1000):
        #selfplay for specific number of rounds, 1000 is the default number 
        for i in xrange(n):
            s.sp.play() 
        s.reset() #in the end reset again
#use the package cPicle to save the dictionary 
    def save(s):
        cPickle.dump(s.learner, open("learn.dat", "w")) #open is for the appointing the name file 
        # w = write, we can even add wb so that it is portable between Windows and Unix 
#use the package cPicle to load the dictionary 
    def load(s):
        s.learner = cPickle.load( open("learn.dat") ) #read the dictionary
        s.sp = Selfplay(s.learner) #selfplay using that dictionary 
        s.reset() # reset at the end
             
class Selfplay:
    def __init__(s, learner = None):
        if learner == None:
            s.learner = Learner(player=2)
        else:
            s.learner = learner
        s.other = Learner(player=1)
        s.i = 0

    def reset(s):
        s.state = State()
        s.learner.reset()
        s.other.reset()

    def play(s):
        s.reset()
        while True:
            s.other.next(s.state)    
            s.learner.next(s.state)
            if s.state.full() or s.state.won(1) or s.state.won(2):
                s.i += 1
                if s.i % 100 == 0:
                    print s.state #hash(s.state)
                    
                if not s.other.traced:
                    s.other.next(s.state)
                break

if __name__ == "__main__":
    print "Tic tac toe - Place game piece using notation g(i,j), i being the row and j being the column"
    print "I.e. g(1,2) places a game piece in the first row, second column."
    print "Write g.selfplay(1000) to have the learner play against itself a 1000 times."
    g = Game()