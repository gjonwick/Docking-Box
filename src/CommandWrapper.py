import subprocess
import sys
from src.decorators import *


class CustomCommand(object):
    command_name = None

    '''
    Receives default args
    '''

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def execute(self, *args, **kwargs):
        print(f'SUPPLIED: *args = [{args}], **kwargs = [{kwargs}]')
        print(f'DEFAULT: *args = [{self.args}], **kwargs = [{self.kwargs}]')

        _args, _kwargs = self._combine_arglist(args, kwargs)
        print(f'Combined _args = [{_args}]')
        print(f'Combined _kwargs = [{_kwargs}]')

        results, p = self._run_command(*_args, **_kwargs)
        return results

    '''
    Combines supplied with defaults, positionals and named seperately, 
    i.e. 
    positional with positional,
    named with named
    '''

    def _combine_arglist(self, args, kwargs):
        print(f'Combining arguments ... [{self.args}] and [{args}], as well as [{self.kwargs} and {kwargs}]')
        _args = self.args + args
        if sys.version_info < (3, 9, 0):
            _kwargs = {**self.kwargs, **kwargs}
        else:
            _kwargs = self.kwargs | kwargs
        _kwargs.update(kwargs)

        return _args, _kwargs

    def _run_command(self, *args, **kwargs):
        #print(f'Inside _run_command; args = {args}; kwargs = {kwargs}')

        # TODO: add code to handle the case where we want to use PIPE as input (to be discussed)

        # redirect the output to subprocess.PIPE
        # kwargs.setdefault('stderr', subprocess.PIPE)
        # kwargs.setdefault('stdout', subprocess.PIPE)

        print(f'Just before buildingProcess ... ')
        try:
            p = self.buildProcess(*args, **kwargs)
            out, err = p.communicate()  # pass if input will be used here
        except:
            raise

        rc = p.returncode
        return (rc, out, err), p

    def buildProcess(self, *args, **kwargs):

        cmd = self._commandline(*args, **kwargs)
        # cmd = [self.command_name] + self.prepare_args(*args, **kwargs)
        print(f'Inside buildProcess; the command to be run: {cmd}')
        try:
            p = PopenWithInput(cmd)

        except:
            print(f'Error setting up the command')
            raise

        return p

    '''
    Unifies the command_name and the arguments as a command line
    Command_name is given during class (tool) creation in tools.py 
    '''

    @debug_logger
    def _commandline(self, *args, **kwargs):
        print("Inside _commandline; before preparing args!")
        print(f'Inside _commandline; command = {[self.command_name] + self.prepare_args(*args, **kwargs)}')
        return [self.command_name] + self.prepare_args(*args,
                                                       **kwargs)  # because of this, the prints inside the prepare_args will be shown twice in the console output

    def prepare_args(self, *args, **kwargs):
        ''' Modify arguments in a format acceptable by Popen.
        Since Popen doesnt read dictionaries ... i.e. can't read v=True, rather than -v,
        or output="blabla.txt" rather than --output="blabla.txt" '''
        options = []

        print(f'Preparing arguments ... ')
        # pre-process 'dict' arguments
        for option, value in kwargs.items():
            print(f'current option = {option}, value = {value}')

            if not option.startswith('-'):

                if len(option) == 1:
                    option = f'-{option}'
                else:
                    option = f'--{option}'

            if value is True:  # e.g. if user inputed ighn=True, then add to arglist -ighn (works for both - and --, e.g. -o and --output)
                options.append(option)
                continue
            elif value is False:
                raise ValueError('False value detected!')

            if option[:2] == '--':
                options.append(f'{option}={str(value)}')  # GNU style e.g. --output="blabla.txt"
            else:
                options.extend((option, str(value)))  # POSIX style e.g. -o "blabla.txt"

        print(f'Options = {options} and args = {list(args)}')
        print(f'Returning from prepare_args with cmd = {options + list(args)}')
        return options + list(args)  # append the positional arguments

    '''
    Receives execution-time args
    '''

    def __call__(self, *args, **kwargs):
        return self.execute(*args, **kwargs)


class PopenWithInput(subprocess.Popen):

    def __init__(self, *args, **kwargs):
        self.command = args[0]

        super(PopenWithInput, self).__init__(*args, **kwargs)


def create_tool(tool_name, command_name, driver=None):
    tool_dict = {
        'command_name': command_name,
        'driver': driver
    }
    tool = type(tool_name, (CustomCommand,), tool_dict)
    return tool


# class Vina:
#
#     command_list = ['set_receptor', 'set_ligand_from_file', 'set_ligand_from_string', 'set_weights', 'compute_vina_maps',
#                     'load_maps', 'write_maps', 'write_pose', 'write_poses', 'poses', 'energies', 'randomize', 'score',
#                     'optimize', 'dock']
#
#     def __init__(self, sf_name='vina', cpu=0, seed=0, no_refine=False, verbosity=1):
#         self.sf_name = sf_name
#         self.cpu = cpu
#         self.seed = seed
#         self.no_refine = no_refine
#         self.verbosity = verbosity
#         self.__dict__.update(self.load_vina_commands())
#
#     def __str__(self):
#         pass
#
#     def load_vina_commands(self):
#         tools = {}
#         for command_name in self.command_list:
#             tools[command_name] = create_tool(command_name.upper(), command_name, 'vina')()
#
#         return tools
#
# vina = Vina()
# vina.dock()