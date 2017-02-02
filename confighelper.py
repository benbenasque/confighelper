"""confighelper.py provides extended yaml and command-line configuration handling for command-line tools. 

confighelper parses command-line arguments, **and**  a yaml configuration file,  and returns
a single merged dictionary of configuration options.  None-null command-line arguments take precedence 
over those specified in a configuration file.

Furthemore confighelper extends the yaml syntax to allow:
    * nested import statements within a yaml file
    * environment variables specified within a yaml file
    * local variables to be defined and used in composition within a yaml file


If a config file is specified via a ``--config=<file>`` command-line argument, then that file is read and parsed as a dictionary. 
Any other command-line arguments are merged into this.  Docopt is used to marhsall command-line arguments, so any command-line tool
you write must have a docopt-recognised usage string.

Example:
     suppose you write a command-line tool mytool.py::
    
        "mytool.py docstring in docopt recognised format

        Usage:
            mytool.py --config=<file> --option1=<value1>"
    
        import confighelper as conf
        # this will load the configuration from <file>, 
        # and merge in option1: value1 from  the command line
        config = conf.config(__doc__, sys.argv[1:] )"

"""


from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


import sys
import os
import re
import docopt
import yaml
import json

# Supported file format extentions
JSON = ["json"]
YAML = ["yaml", "yml"]

# match rows containing environment vars
EVAR = re.compile('\$\(.*?\)')
# match rows containing local vars
LVAR = re.compile('%\(.*?\)')
# match rows containing config file %[file]
CVAR = re.compile('%\[.*\]')

# basic types that can be referred to by expressions
BASIC_TYPES = [int, float, bool, str]


class ConfigError(Exception):
    pass


def config(docstring, args, format="json"):
    """Parse command-line arguments, load a configuration file if specified, and merge.
    
    Arguments:
        docstring : calling module's docstring in docopt recognised format
        args      : command line arguments i.e. in sys.argv[1:]
        format    : format for parsing configuration files (default json)

    Returns:
        a dictionary merged from command-line and file specified options"""
        
    # parse command-line arguments using docopt
    cargs = docopt.docopt(docstring, args)

    # strip command line arguments of leading '--', as we never specify these
    # in a file
    cargs = {key.lstrip("--"): cargs[key] for key in cargs.keys()}

    # always parse command-line arguments as yaml, as this is less verbose the
    # JSON with all its quotation
    cargs = parse_cmd_args(cargs, format="yaml")

    # if a config file is specified, and is not 'falsy'
    if 'config' in cargs and cargs['config']:
        cfile = _load(cargs['config'])
        # merge the command-line and file based dictionaries
        parent = merge(cargs, cfile)

    # otherwise we just take the command-line arguments
    else:
        parent =  cargs

    conf = expand_conf(parent)
    return conf
    
def expand_conf(parent):        
        
    # now return to configuration as string, and keep replacing any
    # local variable expressions with expansion in parent scope.
    # this restricts local variables to be defined at top-level
    # Stop if the string is unchanged since the last loop, or
    # we hit MAX_LOOPS, to prevent infinite loops
    confstr = yaml.dump(parent)
    previous_confstr = confstr
    MAX_LOOPS = 10
    for n in range(MAX_LOOPS):
        confstr = expand_lvars(confstr, parent, LVAR)
        # if nothing has changed, then we can stop recursing
        if confstr == previous_confstr:
            break
        else:
            previous_confstr = confstr
    

    result = yaml.load(confstr)

    return result
        
        

def dump(data, fmt, **kwds):

    if fmt in JSON:
        out = json.dumps(data, **kwds)
    elif fmt in YAML:
        out = yaml.dump(data, **kwds)
    else:
        out = str(data)

    return out

    
    
def load(fname, evar=EVAR, lvar=LVAR, cvar=CVAR, format=None):

    parent = _load(fname, evar=evar, lvar=lvar, cvar=cvar, format=format)
    conf = expand_conf(parent)
    return conf

def _load(fname, evar=EVAR, lvar=LVAR, cvar=CVAR, format=None):
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

    if format == None:
        format = get_format(fname)
    if format not in JSON + YAML:
        raise ConfigError("config format not supported")

    path, name = os.path.split(fname)

    # if path is blank, assume current working directory
    if path.strip() == "":
        path = os.getcwd()

    # open the filename and read as a string
    confstr = open(fname, 'r').read()

    # expand any nested imports into the string
    confstr = expand_cvar(confstr, cvar, search_paths=[path, '.'])

    # expand any environment variables into the string
    confstr = expand_evar(confstr, os.environ, evar)

    # local variable expansions involves two passes
    # the first pass parses the string to provide a parent dict which is scope
    # for expanding local variables

    # parse as json or yaml
    if format in JSON:
        parent = json.loads(confstr)

    if format in YAML:
        parent = yaml.load(confstr)
        
    return parent



def get_format(filename):
    return filename.split('.')[-1]


def basic_type(value):
    return isinstance(value, tuple(BASIC_TYPES))


def stringy(value):
    return isinstance(value, (str,))


def listy(value):
    return hasattr(value, "__getitem__") and not stringy(value)


def expand(string, scope, expr):
    """ Replaces an expression in string by looking it up in scope

    Arguments
    string -- the string containing expression statements e.g. %(key)
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
        result = result.replace(ex, str(expanded))
    return result


def lookup(string, scope):
    """ lookup an expression string within a scope (dictionary) and return result. If string not found, 
    returns None. Characters 0,1 and -1 are ignored e.g. %(key1) and $(key2) %[key3] become key1 and key2 and key3."""

    name = string[2:-1]
    if name in scope:
        result = scope[name]
        if not basic_type(result):
            raise Exception("expressions must refer to strings or values with a basic type: %s resolves to type %s" % (
                string, type(result)))
        return result


def isdict(node):
    return isinstance(node, dict)


def isleaf(node):
    return not isdict(node) and not islist(node)


def islist(node):
    return isinstance(node, list)


def expand_evar(s, env, expr):
    """search through a string to find any environment variable expressions and expand into s"""
    vars = expr.findall(s)
    for v in vars:
        vname = v[2:-1]
        if vname in env:
            s = s.replace(v, env[vname])
        else:
            pass
    return s


def expand_cvar(s, expr, search_paths=['.']):
    """search through a string to find any import expressions and load them into s, looking in specified search paths"""

    vars = expr.findall(s)
    for v in vars:
        fname = v[2:-1]
        found = False
        for path in search_paths:
            fullname = os.path.join(path, fname)
            if not os.path.exists(fullname):
                continue
            else:
                substring = expand_cvar(open(fullname, 'r').read(), expr)
                s = s.replace(v, substring)
                found = True
        if not found:
            raise IOError(
                "import %s: file not found on any search path" % fname)
    return s


def expand_lvars(s, scope, expr):
    vars = expr.findall(s)
    for v in vars:
        vname = v[2:-1]
        if vname in scope:
            s = s.replace(v, str(scope[vname]))
        else:
            pass
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
    if v1 != None:
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
    # exp = re.compile("(\[.*\]) | (\{.*\})")
    # lexpr = re.compile("\[.*\]")
    # dexpr = re.compile("\{.*\}")

    if format in JSON:
        import json
    elif format in YAML:
        import yaml
    else:
        raise ConfigError(
            "configuration format: %s not understood, use json or yaml" % format)

    for (k, v) in args.items():
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
