"""confighelper.py provides general configuration handling. 

Dependencies: json or yaml, docopt

confighelper.py allows options to be specified in a json or yaml config file, specified by a --config=<file> option, 
**and** allows options to be specified at the command line. File-specified and command-line specified options will be
merged into a single dictionary, with none-null command-line options taking precedence over file-specified.
Only those command-line arguments specified in the docstring can be given at the command line, while anything
can be put into a configuration file. It is up to the user to keep the docstring up-to-date.

Furthermore, configuration files can import other configuration files, can refer to environment variables and variables defined
elsewhere in the configuration file.  

To use this module, import and call the confighelper.config function,  passing in the calling module's docstring
and command-line arguments e.g.
    
    example.py
    "mymodule.py docstring in docopt recognised format see docopt"
    
    import confighelper as conf
    config = conf.config(__doc__, sys.argv[1:] )

If ** and only if ** a --config option is supplied at the command-line, this will be read and parsed, and merged with any 
other command-line arguments. 
    
A potential "gotcha" is that any defaults specified using the docopt docstring will override those specified in the config file, 
since they will be supplied as command-line arguments, even if they are not supplied at the command line.
Therefore it is preferrable **not** to specify defaults in the docstring, but place them in a defaults config file. 

Command-line options are stripped of preceding "--", to allow the equivalent file options to be specified without a leading "--". 

Expression expansion. Confighelper recognises three types of expression:
 * environment variables using $(var) syntax
 * configuration files using %[file] syntax
 * local variables using %(var) syntax
 
 A configuration file consists of (key, value) pairs. If a configuration file expression appears as a key, then it will
 be read, parsed, and the original (key, value) pair will be replaced by the parsed dictionary.  In other words, the original 
 value is treated as null, and the statement functions much like an import statement.  If a configuration file 
 expression appears as a value, then it will be read, parsed, and the original value replaced by the parsed dictionary.

The order of expansion is as follows:

 1. Parent configuration file is read as string
 2. Any environment variable expressions are expanded
 3. Any configuration file expressions are recursively loaded
 4. Any local variable expressions are expanded by lookup in the parent scope.
 
 
This module itself can be run from the command line:

Usage: 
    confighelper.py [--config=<file>] [options]

Options:
        --config=<file>    configuration file to specify options"""


from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals        
        
        
import sys
import os
import re
import docopt
from collections import OrderedDict
import pprint
import yaml
import json

# Supported file format extentions
JSON = ["json"]
YAML = ["yaml", "yml"]    

EVAR  = re.compile('\$\(.*?\)')                              # match rows containing environment vars
LVAR  = re.compile('%\(.*?\)')                               # match rows containing local vars 
CVAR =  re.compile('%\[.*\]' )                               # match rows containing config file %[file]

BASIC_TYPES = [int,float, bool, str]                 # basic types that can be referred to by expressions

class ConfigError(Exception):
    pass


def main():
 
    c = config(__doc__, sys.argv[1:] )
    
    print(dump(c,"yaml",indent=4))
    
    #print(json.dumps(c, indent=4, default=date_handler))
   

def config(docstring, args, format="json"):
    """ this is the primary function, which takes a modules's docstring, 
    a list of command line arguments (as in sys.argv[1:]) and returns a 
    merged dictionary which is the result of reading any file specified
    by a --config argument, and then merging into that any other command-line
    arguments. 
    
    Arguments:
    docstring -- calling module's docstring in docopt recognised format
    args      -- command line arguments as in sys.argv[1:]
    format    -- format for parsing configuration files (default json)"""
    
    # parse command-line arguments using docopt
    cargs  = docopt.docopt(docstring,args)
        

    # strip command line arguments of leading '--', as we never specify these in a file
    cargs = {key.lstrip("--"): cargs[key] for key in cargs.keys()}
    
    # always parse command-line arguments as yaml, as this is less verbose the JSON with all its quotation
    cargs = parse_cmd_args(cargs, format="yaml")

    # if a config file is specified, and is not 'falsy'
    if 'config' in cargs and cargs['config']:
        cfile = load(cargs['config'])
        merged = merge(cargs, cfile)
        return merged
    else:
        return cargs



def dump(data, fmt, **kwds):

    if fmt in JSON:
        out = json.dumps(data, **kwds)
    elif fmt in YAML:
        out = yaml.dump(data, **kwds)
    else:
        out = str(data)
        
    return out
    
def load(fname, evar=EVAR, lvar=LVAR, cvar=CVAR, format=None):
    """Loads a config file, and recursively opens any included config files 
    
    Arguments:
    fname -- name of the file to load
    evar  -- regular expression matching environment variable definition
    lvar  -- regular expression matching local variable definition
    cvar  -- regular expression matching included config file  definition
    format -- format to use for config file, json or yaml, default determine by file extension
    
    Suppose in the parent we have:
        
        option1: value1
        option2: value2
        option3: %(config2.yaml)
    
    
    where config2.yaml looks like:
    
        option2: value3
        option4: value4
    
    Then config2.yaml will be read and parsed. If flatten is false, the resulting dictionary
    will look like:
    
        option1: value1
        option2: value2
        option3:
            option2: value3
            option4: value4

    Whereas if flatten=true, then config2 will **update** the parent, delete the key which held the file,
    potentially overwriting values:
    
    option1: value1
    option2: value3
    option4: value4 
    
    This second option can be used like an include directive by specifying exlusive keys e.g.
    include1: config1.yaml
    include2: config2.yaml
    include3: config3.yaml"""
    
    
    
    if format==None:
        format = get_format(fname)
    if format not in JSON + YAML:
        raise ConfigError("config format not supported")
    
    path, name = os.path.split(fname)
    
	# if path is blank, assume current working directory
    if path.strip()=="":
        path = os.getcwd()
	
    # open the filename and read as a string
    confstr = open(fname, 'r').read()
    
    # expand any nested imports into the string
    confstr = expand_cvar(confstr, cvar)

    # expand any environment variables into the string
    confstr = expand_evar(confstr, os.environ, evar)

    # parse as json or yaml
    if format in JSON:
        parent=json.loads(confstr)
    
    if format in YAML:
        parent = yaml.load(confstr)
   
    
    # take really low-level approach to expansion here which involves two passes
    # parse the string as a dict, then use that to replace any local variables with
    # entries in the dictionary. Restricts local variables to be defined at top-level
    # This is ugly, should be a recursive functionm but implemented here as a fixed
    # number of expansions
    for n in range(10):
        confstr = expand_lvars(confstr, parent, lvar)
        
        

    if format in JSON:
        result = json.loads(confstr)
    
    if format in YAML:
        result = yaml.load(confstr)
        
    return result
    # expand any local variable definitions, i.e. nodes in the graph that refer to each other
    #tree = parent.copy()
    #scope = parent.copy()
    #result = expand_tree(tree, scope, lvar)
    #return result


def get_format(filename):
    return filename.split('.')[-1]

    
def basic_type(value):
    return type(value) in BASIC_TYPES
        
def stringy(value):
    return isinstance(value, (str,))

def listy(value):
    return hasattr(value, "__getitem__") and not stringy(value)    


def expand(string, scope, expr):
    """ Replaces an expression in string by looking it up in scope
    
    Arguments
    string -- the string containing expressions e.g. %(key)
    scope  -- dictionary to lookup keys in
    expression -- a regular expression which matches expressions
    
    Returns -- the original string with all resolveable expressions replaced"""
    
    result = string
    # if no local variable definitions in string
    if not expr.search(result):
        return result
    
    # loop through each local variable 
    exprs = expr.findall(string)
    for ex in exprs:
        expanded = lookup(ex, scope)
        
        # if nothing is found, we can stop looking
        if not expanded:
            continue

        # otherwise we test whether there are still expressions in the string
        elif stringy(expanded) and expr.search(expanded):
            expanded = expand(expanded, scope, expr)
        result   = result.replace(ex, str(expanded))
    return result

def lookup(string, scope):
    """ lookup an expression string within a scope (dictionary) and return result. If string not found, 
    returns None. Characters 0,1 and -1 are ignored e.g. %(key1) and $(key2) %[key3] become key1 and key2 and key3."""
    
    name = string[2:-1]
    if name in scope:
        result = scope[name]
        if not basic_type(result):
            raise Exception("expressions must refer to strings or values with a basic type: %s resolves to type %s" %(string, type(result)))
        return result


def isdict(node):
    return type(node)==type({})

        
def isleaf(node):
    return not isdict(node) and not islist(node)

def islist(node):
    return type(node)==type([])

    
def expand_tree(tree, scope, expr):
    if isleaf(tree): 
        return tree

    for key, node in tree.items():

        if isleaf(node):
            new_node = expand_leaf(node, scope, expr)
       
        elif islist(node):
            new_node = [expand_tree(n,scope,expr) for n in node]
        
        elif isdict(node):
            new_node = expand_tree(node, scope, expr)
        
        tree[key] = new_node
    return tree    

    
def expand_leaf(node, scope, expr):
    if stringy(node):
        return expand(node, scope, expr)
    elif listy(node):
        f = lambda n: expand_leaf(n, scope, expr)
        return map(f, node)
    else:
        return node


def expand_evar(s, env, expr):
    """search through a string to find any environment variable expressions and expand into s"""
    vars = expr.findall(s)
    for v in vars:
        vname = v[2:-1]
        if vname in env:
            s = s.replace(v, env[vname])
        else: pass
    return s

def expand_cvar(s, expr):
    """search through a string to find any import expressions and load them into s"""

    vars = expr.findall(s)
    for v in vars:
        fname = v[2:-1]
        if os.path.exists(fname):
            substring = expand_cvar(open(fname, 'r').read(), expr)
            s = s.replace(v, substring)
    return s
    
    
def expand_lvars(s, scope, expr):
    vars = expr.findall(s)
    for v in vars:
        vname = v[2:-1]
        if vname in scope:
            print(vname)
            print(scope[vname])
            s = s.replace(v, str(scope[vname]))
        else: pass
    return s
    

def merge(dict_1, dict_2):
    """Merge two dictionaries.    
    Values that evaluate to true take priority over falsy values.    
    `dict_1` takes priority over `dict_2`.    """    
    
    # values that are None do not override
    return dict((str(key), choose(key, dict_1, dict_2)) for key in set(dict_2) | set(dict_1))
    

            
def choose(key, dict1, dict2):
    v1 = dict1.get(key)
    v2 = dict2.get(key)
    if v1!=None:
        return v1
    else:
        return v2

def parse_cmd_args(args, format="json"):
    """Parse command line arguments as json/yaml
    
    Arguments: 
        args -- a dictionary mapping argument names to their values
        
    Returns:
        a new dictionary with any list-like values expanded"""
    
    jargs = {}
    
	# match list expression or dictionary expression
    exp = re.compile("(\[.*\]) | (\{.*\})")
    lexpr =  re.compile("\[.*\]")
    dexpr =  re.compile("\{.*\}")

    
    if format in JSON:
        import json
    elif format in YAML:
        import yaml
    else:
        raise ConfigError("configuration format: %s not understood, use json or yaml" % format)

    for (k,v) in args.items():
        #if v and type(v)==type("") and ( lexpr.match(v) or dexpr.match(v)):
        if v and stringy(v):

            if format in JSON:
                jv = json.loads(v)
            elif format in YAML:
                jv = yaml.load(v)


            jargs[k] = jv
        else:
            jargs[k] = v

    return jargs
         
  
    
if __name__ == '__main__':
    main()
        
