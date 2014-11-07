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
		--option1=arg1     anything specified here will ovveride the config file 
		--option2=arg2
		--option3=arg3
		--option4=arg4
		--option5=arg5
"""
    
import confighelper as conf
import sys
config = conf.config(__doc__, sys.argv[1:] )

# config will be a merged dictionary of file and command-line args
print config