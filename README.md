==========================================================
confighelper.py
===========================================================
convenient file and command-line based configuration handling
Author: Sam Hawkins, sam@computing.io

## Quick start

    $> git clone https://github.com/samwisehawkins/confighelper.git
	$> cd confighelper/example
	$> python example.py --config=config.yaml 

    {   'config': 'config.yaml',
        'option1': 'a',
        'option2': 'option2.1 : x option2.2 : y ',
        'option3': 3.0,
        'option3.1': 'foo',
        'option3.2': 'bar',
        'option4': '/project/slha',
        'option5': 'a',
        'ordered': [   {   'option8': 'test ordering'},
                       {   'option7': 'original key orders preserved'},
                       {   'option6': {   'a': 'even with nesting',
                                          'b': 'in some levels'}}]}

    
     $>python example.py --config=config.yaml --option3=bar --option5=baz

    {   'config': 'config.yaml',
        'option1': 'a',
        'option2': 'option2.1 : x option2.2 : y ',
        'option3': 'bar',
        'option3.1': 'foo',
        'option3.2': 'bar',
        'option4': '/project/slha',
        'option5': 'baz',
        'ordered': [   {   'option8': 'test ordering'},
                       {   'option7': 'original key orders preserved'},
                       {   'option6': {   'a': 'even with nesting',
                                          'b': 'in some levels'}}]}


What just happened? [This parent config file](example/config.yaml), imported 
[another configuration file](example/c2.yaml), and command-line arguments were merged into the result.
                
        
## Description

`confighelper.py` allows options to be supplied in a yaml config file specified by a `--config=<file>` option.
Options can also be specified at the command line, and will be merged and override those in the file. 
The result is a single configuration dictionary.

The [docopt](https://github.com/docopt/docopt) module is used to marshall
command-line arguments.  **This means that only those options defined in the docstring will
be accepted at the command-line**

Furthermore, configuration files can:

* import other configuration files
    - using %[file] syntax
* reference environment variables
    - using $(VAR) syntax
* reference variables defined elsewhere in the config file
    - using %(key) syntax
    - only variables defined at top-level can be referenced
    - allows variables defined elsewhere to be combined, e.g. `%(path)/myfiles`

Note that yaml does not allow entries to start with the "%" character, so you may need to put quotes around entries.
    
## Dependencies

* [yaml](http://pyyaml.org/)
* [docopt](https://github.com/docopt/docopt) (version 0.6 is bundled, as 0.7 is going to break interface)


## Usage

To use in your own module, write a docopt recognisable docstring, including a  `--config=<file>` option. 
    
    """docopt recognised docstring
    
    Usage:
        example.py [--config=<file>]
                   [--option1=arg1] # allow option1 to be specified at command-line"""

    import confighelper as conf
    config = conf.config(__doc__, sys.argv[1:] )
    
Voila! Command-line and yaml options have been merged.    

# Rules

## Command-line option stripping

Command-line options are stripped of any preceding "--".  This allow the equivalent options to be specified in a file without a leading "--". 

## Precedence and defaults

**Command-line arguments take precedence over configuration files**. A consequence is that any **defaults** s
pecified using the docopt docstring will override those specified in the config file.
Therefore it is often preferrable **not** to specify defaults in the docstring, but place them in an example configuration file.


## Expressions

Confighelper recognises three types of expression:
 * environment variables using `$(var)` syntax
 * import statements using `%[file]` syntax
 * local variables (defined elsewhere in the file) using `%(var)` syntax
 
The order of expansion of expressions is as follows:

 1. Parent configuration file is read as string
 2. Any import statements are expanded if the files exist
 3. Any environment variable expressions are expanded
 4. Resulting string is parsed as yaml to give dictionary
 5. Any local variable expressions are expanded by lookup in the outer scope.