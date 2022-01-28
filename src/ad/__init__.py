""" Python binding with AutoDock. """
from src.CommandWrapper import *


class AutoDock:
    command_list = ['prepare_receptor', 'prepare_ligand', 'prepare_flexreceptor.py', 'ls']

    # Reminder: self.__dict__ contains all attributes defined for the object.
    def __init__(self):
        self.__dict__.update(self.load_ad_commands())

    def load_ad_commands(self):
        tools = {}
        for command_name in self.command_list:
            tools[command_name] = create_tool(command_name.upper(), command_name, '')

        return tools


ad = AutoDock()
# globals().update(load_ad_commands())
