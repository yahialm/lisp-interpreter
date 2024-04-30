# Lisp Interpreter by Me: @YahiaLamhafad

class FuncReturn(Exception):
    def __init__(self, val):
        super().__init__('`return` outside a function')
        self.val = val


class LoopBreak(Exception):
    def __init__(self):
        super().__init__('`break` outside a loop')


class LoopContinue(Exception):
    def __init__(self):
        super().__init__('`continue` outside a loop')


#Atom handling 
def parse_atom(s):
    import json
    try:
        return ['val', json.loads(s)]
    except json.JSONDecodeError:
        return s

# the function used to look for value of the no list nodes which are variable names
def name_loopup(env, key):
    while env: # linked list traversal
        current, env = env # current var gets the current scope list (which contains key-value pairs) and env gets the nested ones 

        if key in current:
            return current
    raise ValueError('undefined name')

#skip spaces
def skip_space(s: str, idx: int) -> int:

    while True:
        save = idx

        #skip white spaces
        while idx < len(s) and s[idx].isspace():
            idx+=1
        
        #skip a line comment
        if idx < len(s) and s[idx] == ";" :
            idx += 1
            # Skip chars since no EOL (--> \n)  is found
            while idx < len(s) and s[idx] != "\n" :
                idx += 1
        
        #no more spaces or comments
        if idx == save:
            break

    return idx

# Just note the parse function in case we need it
def parse_expr(s: str, idx: int):
    idx = skip_space(s, idx)
    if s[idx] == '(':
        # a list
        idx += 1
        l = []
        while True:
            idx = skip_space(s, idx)

            # Unbalanced parenthesis, for string='(' or string='(_whitespace_'
            # Note that the check focus on parenthesis but not the chars
            if idx >= len(s):
                raise Exception('unbalanced parenthesis')
            
            # Balanced parenthesis
            if s[idx] == ')':
                idx += 1
                break

            idx, v = parse_expr(s, idx)
            l.append(v)
        return idx, l
        
    # Bad parenthesis
    elif s[idx] == ')':
        raise Exception('bad parenthesis')

    else:
        #is atom
        start = idx
        while idx < len(s) and (not s[idx].isspace()) and s[idx] not in '()':
            idx += 1
        if start == idx:
            raise Exception('empty program')
        return idx, parse_atom(s[start:idx])

###############################################

# 2. Control flows. Like conditionals and loops. (IF-THEN-ELSE and LOOP)

################################################

######### Control flow and Loops ##########
    

def pl_eval(env, node):

    ###New code

    # read a variable
    if not isinstance(node, list):
        assert isinstance(node, str)
        return name_loopup(env, node)[node]
    
    # Nodes that aren't lists are those variable names, for example (+ x y), x and y are nodes but are not lists, so strings, so we have to find their values within the env variable where values are stored by scope
    # Think of a env variable like: 

    """ looks like 
    env = (
    {'x': 5, 'y': 10},  # Mapping of variables in the current scope
        (
            {'z': 15},  # Mapping of variables in the nested scope
            (
                {'a': 20},  # Mapping of variables in the further nested scope
                None  # Reference to the parent environment (None indicates the top-level scope) !!!!!!!!!!!!!!!!!!!
            )
        )
    )
    """

    # Note that the env is a linked list
    
    # new scope
    if node[0] in ('do', 'then', 'else') and len(node) > 1:
        new_env = (dict(), env) # add the map as the linked list head
        for val in node[1:]:
            val = pl_eval(new_env, val)
        return val # the last item
    
    if len(node) == 0:
        raise ValueError('empty list')
    
    # New variable
    if node[0] == 'var' and len(node) == 3:
        _, name, val = node
        scope, _ = env
        if name in scope:
            raise ValueError('duplicated name')
        val = pl_eval(env, val)
        scope[name] = val
        return val
    
    # update a variable
    if node[0] == 'set' and len(node) == 3:
        _, name, val = node
        scope = name_loopup(env, name)
        val = pl_eval(env, val)
        scope[name] = val
        return val
    
    # bool, number, string and etc
    if len(node) == 2 and node[0] == 'val':
        return node[1]
    
    # binary operators
    import operator
    binops = {
        '+': operator.add,
        '-': operator.sub,
        '*': operator.mul,
        '/': operator.truediv,
        'eq': operator.eq,
        'ne': operator.ne,
        'ge': operator.ge,
        'gt': operator.gt,
        'le': operator.le,
        'lt': operator.lt,
        'and': operator.and_,
        'or': operator.or_,
    }


    if len(node) == 3 and node[0] in binops:
        op = binops[node[0]]
        return op(pl_eval(env, node[1]), pl_eval(env, node[2]))


    # unary operators
    unops = {
        '-': operator.neg,
        'not': operator.not_,
    }

    if len(node) == 2 and node[0] in unops:
        op = unops[node[0]]
        return op(pl_eval(env, node[1]))


    # conditionals

    # The if command is similar to the (? yes no) operator in the calculator chapter. Except that the “else” part is optional. So the code is modified to handle both of them.

    """ Old implementation
    if len(node) == 4 and node[0] == '?':
        _, cond, yes, no = node
        if pl_eval(env, cond):
            return pl_eval(env, yes)
        else:
            return pl_eval(env, no)
    """
    # '_' is a valid variable name in python, but it's used for special convention which is that the value isn't intended to be used or it's not relevant : throwaway variable

    if len(node) in (3, 4) and node[0] in ('?', 'if'):
        _, cond, yes, *no = node
        no = no[0] if no else ['val', None] # the `else` part is optional
        new_env = (dict(), env) # new scope
        if pl_eval(new_env, cond):
            return pl_eval(new_env, yes)
        else:
            return pl_eval(new_env, no)
        

    """
    Loop Syntax in LISP programming language
    ---->    (loop condition body)
        (break)
        (continue)
    """

    # loop
    # Old implementation before considering "break" and "continue" statements
    """if node[0] == 'loop' and len(node) == 3:
        _, cond, body = node

        #Having a return is essentiel so our recursive function can properly run
        ret = None
        
        while True:

            #New env for (cond and body)
            new_env = (dict(), env)
            
            #Check if the condition still true: if no 'break' to exit the loop
            if not pl_eval(new_env, cond):
                break
            
            #While the condition still true, the body still executed
            ret = pl_eval(new_env, body)
        
        return ret
    """    
    
    
    # loop ( with break and continue)
    if node[0] == 'loop' and len(node) == 3:
        _, cond, body = node

        #Having a return is essentiel so our recursive function can properly run
        #Note that ret is so important since this function may raise an error which is not a return that we can consider for our recursive function 
        ret = None
        
        while True:

            #New env for (cond and body)
            new_env = (dict(), env)
            
            #Check if the condition still true: if no 'break' to exit the loop
            if not pl_eval(new_env, cond):
                break
            
            #While the condition still true, the body still executed
            #Using try-except
            try:
                ret = pl_eval(new_env, body)

            
            #If any exception is raised: 
                
            #Break
            except LoopBreak:
                break
            
            #Continue
            except LoopContinue:
                continue
        
        return ret
    

    # break & continue
    if node[0] == 'break' and len(node) == 1:
        raise LoopBreak
    
    if node[0] == 'continue' and len(node) == 1:
        raise LoopContinue
    

    ########Functions########

    # function definition
    if node[0] == 'def' and len(node) == 4:
        _, name, args, body = node

        # sanity checks

        ## checks args syntax
        for arg_name in args:
            if not isinstance(arg_name, str):
                raise ValueError('bad argument name')

        ## Checks for duplicated args
        if len(args) != len(set(args)):
            raise ValueError('duplicated arguments')

        # add the function to the scope
        dct, _ = env

        ##Overloading purpose: Functions with the same name can coexist but only with different args number
        key = (name, len(args))  
        
        ##Checks for any existing funcs with same properties
        if key in dct:
            raise ValueError('duplicated function')
        
        ## Saving the body because It's needed for func calls, env also because our func may use some already defined vars
        dct[key] = (args, body, env)

        return



    #Function call
    if node[0] == 'call' and len(node) >= 2:
        _, name, *args = node
        key = (name, len(args))
        fargs, fbody, fenv = name_loopup(env, key)[key]

        # args, creating a new scope to assign each var name to its correspndant value
        new_env = dict()
        for arg_name, arg_val in zip(fargs, args):
            new_env[arg_name] = pl_eval(env, arg_val)

        # call, execute the body of the function using the created scope and and the existing one for any extern var/value
        try:
            return pl_eval((new_env, fenv), fbody)
        except FuncReturn as ret:
            return ret.val
        
    #return 
    if node[0] == 'return' and len(node) == 1:
        raise FuncReturn(None)
    if node[0] == 'return' and len(node) == 2:
        _, val = node
        raise FuncReturn(pl_eval(env, val))


    # print
    if node[0] == 'print':
        return print(*(pl_eval(env, val) for val in node[1:]))
    
    raise ValueError('unknown expression')

#########################################################################

#High level implementation

def pl_parse(s):

    idx, node = parse_expr(s, 0)
    #idx = skip_space(s, idx)
    if idx < len(s):
        raise ValueError('trailing garbage')
    return node

#The interpreter accepts a sequence of expressions instead of a single expression. This is done by wrapping the input with a do command.
def pl_parse_prog(s):
    return pl_parse('(do ' + s + ')')

#################Test###################

#program = '''(def func (a) (if (lt a 0) (do (print "yes") ) (else (print "no") ) ) ) (call func 2)'''
program = '''(def func (n)
                (if (le n 0)
                (then 0)
                (else (return n))
                )
            )
            (print (call func 5))
        '''
ss = pl_eval(({},(None)), pl_parse_prog(program))


###################Test-1######################

def test_eval():
    def f(s):
        return pl_eval(None, pl_parse_prog(s))
    assert f('''
        (def fib (n)
            (if (le n 0)
                (then 0)
                (else (+ n (call fib (- n 1))))))
        (call fib 5)
    ''') == 5 + 4 + 3 + 2 + 1
    assert f('''
        (def fib (n) (do
            (var r 0)
            (loop (gt n 0) (do
                (set r (+ r n))
                (set n (- n 1))
            ))
            (return r)
        ))
        (call fib 5)
    ''') == 5 + 4 + 3 + 2 + 1 