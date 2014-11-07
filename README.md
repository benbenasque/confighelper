==========================================================
confighelper.py
===========================================================

## Intro
confighlper.py allows you to specify python configurations in a 
yaml file AND/OR at the command-line, with command-line arguments 
overwriding those in the file.

## Description

confighelper.py allows options to be specified in a json or yaml config file, specified by a --config=<file> option, 
**and** allows options to be specified at the command line. File-specified and command-line specified options will be
merged into a single dictionary, with none-null command-line options taking precedence and overriding the same specified
within a file. 

Only those command-line arguments specified in the modules docstring 
(using the docopt format) can be given at the command line, while anything
can be put into a configuration file. It is up to the user to keep the docstring up-to-date.

Furthermore, configuration files can import other configuration files, 
can refer to environment variables and variables defined
elsewhere in the configuration file.  
It also allows the use of environment variables within configurations,
locally defined variables being reused, and nested configuration files.

## Motivation

It was borne out of my frustration of not finding a configuration 
file format for for python which was:
* human readable and supported comments
* allowed over-riding at the command-line to support quick changes

I combined the awesomeness of docopt with the awesomeness of yaml.

## Dependencies

json or yaml, docopt

# Usage

To use this module, import and call the confighelper.config function,  passing in the calling module's docstring
and command-line arguments.  Look in the example subdirectory and try:

    $> python mymodule.py --config=simple.yaml --option2=hello

    
    mymodule.py
    """mymodule.py docstring in docopt recognised format see docopt
        Usage: 
        mymodule.py [--config=<file>]
                [--option1=arg1]
                [--option2=arg2]
                [--option3=arg3]
                [--option4=arg4]
                [--option5=arg5]
    
        Options:
            --config=<file>    configuration file to specify options
            --config-fmt=<fmt> configuration file format [default: JSON]
            --option1=arg1     anything specified here will ovveride the config file 
     """
    
    import confighelper as conf
    config = conf.config(__doc__, sys.argv[1:] )
    # config will be a merged dictionary of file and command-line args
    print config
    
Suppose we have the following (simple) configuration file (note lack of preceeding '--')

    myconfig.yaml
    option1: a
    option2: b
    option3: c
    option4: d
    option5: e

Then run mymodule.py:

    $>python mymodule.py --config=myconfig.yaml --option3=xyz


If ** and only if ** a --config option is supplied at the command-line, this will be read and parsed, and merged with any 
other command-line arguments.  

A potential "gotcha" is that any **defaults** specified using the docopt docstring will override those specified in the config file, 
since defaults will be supplied as command-line arguments, even if they are not defined on the command line.
Therefore it is preferrable **not** to specify defaults in the docstring, but place them in a defaults config file. 

Command-line options are stripped of preceding "--", to allow the equivalent file options to be specified without a leading "--". 

## Expression expansion. 


Confighelper recognises three types of expression:
 * environment variables using $(var) syntax
 * configuration files using %[file] syntax
 * local variables using %(var) syntax
 
 A configuration file consists of (key, value) pairs. If a configuration file expression appears as a key, then it will
 be read, parsed, and the original (key, value) pair will be replaced by the parsed dictionary.  In other words, the original 
 value from the (key,value) pair is ignored.  This usage behaves much like an import statement.  If a configuration file 
 expression appears as a value, then it will be read, parsed, and the original value replaced by the parsed dictionary, still
 attached to the original key. This allows hierechical configurations.

The order of expansion of expressions is as follows:

 1. Parent configuration file is read as string
 2. Any environment variable expressions are expanded
 3. Any configuration file expressions are recursively loaded
 4. Any local variable expressions are expanded by lookup in the parent scope.
 
 
## Nested example

Coming soon
