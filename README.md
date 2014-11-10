==========================================================
confighelper.py
===========================================================
convenient file and command-line based configuration handling
Author: Sam Hawkins, sam@computing.io

## Quick start

Quickest way to learn is by example. Suppose we have [this parent config file](example/config.yaml), which also refers to 
[another configuration file](example/c2.yaml). Then we call the example with the '--config' option specifying the file, 
and command-line arguments:


    $> git clone https://github.com/samwisehawkins/confighelper.git
	$> cd confighelper/example
	$> python example.py --config=config.yaml --option2=foo  --option5=bar
    {   'config': 'config.yaml',
        'option1': 'a',
        'option2': 'foo',
        'option3': 3.0,
        'option4': '/home/sam',
        'option5': 'bar'}


## Description
`confighelper.py` allows options to be specified in config file, specified by a special `--config=<file>` option.
Options can also be specified at the command line, and will override those in the file. 
The result is a single dictionary.

The [docopt](https://github.com/docopt/docopt) modue is used to marshall
command-line arguments.  That means only options defined in the modules docstring will
be accepted at the command-line. 

Furthermore, configuration files can:

* import other configuration files, 
* reference environment variables
* reference vriables defined elsewhere in the config file


## Dependencies

* json or [yaml](http://pyyaml.org/)
* [docopt](https://github.com/docopt/docopt)


## Usage

Write a docstring following the [docopt](http://docopt.org/) syntax. Import
`confighelper.py`, and call `confighelper.config(docstring)`. 


Example  

    example.py
    """example.py simple example to illustrate use of confighelper
	   docstring in docopt recognised format
       
	   Usage: 
        mymodule.py [--config=<file>]
                [--option1=arg1]
                [--option2=arg2]
                [--option3=arg3]
                [--option4=arg4]
                [--option5=arg5]
    
        Options:
            --config=<file>    configuration file to specify options
            --config-fmt=<fmt> configuration file format (JSON or YAML) [default: JSON]
            --option1=arg1     anything specified here will ovveride the config file 
            --option3=arg3
            --option4=arg4
            --option5=arg5
	"""
    
    import confighelper as conf
    config = conf.config(__doc__, sys.argv[1:] ) # parse and merge file-based and command-line args
    print config


A potential "gotcha" is that any **defaults** specified using the docopt docstring will override those specified in the config file, 
since defaults will be supplied as command-line arguments even if they are not defined on the command line.
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


