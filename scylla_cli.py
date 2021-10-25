"""
Simple Scylla REST API client module
"""

import logging
import re
import json
from argparse import ArgumentParser
import requests

from rest.scylla_rest_client import ScyllaRestClient

log = logging.getLogger('scylla.cli')

"""
A dictionary that keeps the insertion order
"""
class OrderedDict:
    def __init__(self):
        self._pos = 0
        self._count = 0
        self._cur_pos = 0

        self.by_key = dict()
        self.by_pos = dict()

    def insert(self, key, value):
        assert type(key) is not int
        self.by_key[key] = value
        self.by_pos[self._pos] = key
        self._pos += 1
        self._count += 1

    def __add__(self, key, value):
        self.insert(key, value)

    def __getitem__(self, idx_or_key):
        if type(idx_or_key) is int:
            if idx_or_key not in self.by_pos:
                raise IndexError('OrderedDict index out of range')
            key = self.by_pos[idx_or_key]
        else:
            key = idx_or_key
        return self.by_key[key]

    def __repr__(self):
        s = ''
        for key in self.keys():
            if s:
                s += ', '
            value = self.by_key[key]
            s += f"{{{key}: {value}}}"
        return f"OrderedDict({s})"

    def __len__(self):
        return len(self.by_key)

    def __iter__(self):
        self._cur_pos = 0
        return self

    def __next__(self):
        next_key = self.by_pos[self._cur_pos]
        self._cur_pos += 1
        if self._cur_pos >= self._count:
            raise StopIteration
        return next_key

    def count(self) -> int:
        return self._count

    def keys(self):
        for i in range(0, self._pos):
            if i not in self.by_pos:
                continue
            yield self.by_pos[i]

    def items(self):
        for key in self.keys():
            yield self.by_key[key]

class ScyllaApiOption:
    # init Command
    def __init__(self, name:str, required:bool = False, param_type:str='query',
                 allowed_values=[], help:str=''):
        self.name = name
        self.required = required
        self.param_type = param_type
        self.allowed_values = allowed_values
        self.help = help
        log.debug(f"Created {self.__repr__()}")

    def __repr__(self):
        return f"ApiCommandOption(name={self.name}, required={self.required}, param_type={self.param_type}, allowed_values={self.allowed_values}, help={self.help})"

    def __str__(self):
        return f"option_name={self.name}, required={self.required}, param_type={self.param_type}, allowed_values={self.allowed_values}, help={self.help}"

    def add_argument(self, parser:ArgumentParser):
        parser.add_argument(f"--{self.name}", dest=self.name, help=self.help, nargs=1, choices=self.allowed_values if self.allowed_values else None)

class ScyllaApiCommand:
    class Method:
        GET = 0
        POST = 1
        DELETE = 2
        kind_to_str = ['GET', 'POST', 'DELETE']
        str_to_kind = {
            'GET': GET,
            'POST': POST,
            'DELETE': DELETE,
        }

        def __init__(self, kind=GET, desc:str='', command_name:str='', options:OrderedDict=None):
            self.kind = kind
            self.command_name = command_name
            self.desc = desc
            self.options = options or OrderedDict()
            self.parser = None
            log.debug(f"Created {self.__repr__()}")

        def __repr__(self):
            return f"Method(kind={self.kind_to_str[self.kind]}, desc={self.desc}, options={self.options})"

        def __str__(self):
            s = f"{self.kind_to_str[self.kind]}: {self.desc}"
            #for opt_name in self.options.keys():
            #    opt = self.options[opt_name]
            #    s += f"\n        {opt}"
            return s

        def add_option(self, option:ScyllaApiOption):
            self.options.insert(option.name, option)

        def generate_parser(self):
            parser = ArgumentParser(description=f"{self.command_name} {self.kind_to_str[self.kind]} API syntax.", add_help=False)
            for opt in self.options.items():
                opt.add_argument(parser)
            self.parser = parser

        def get_help(self):
            s = f"{self.kind_to_str[self.kind]} {self.command_name}"
            required_help = ''
            optional_help = ''

            def opt_help(name:str, param:str='', help:str='', justify=21):
                pfx = f"  {name} {param}"
                s = pfx.ljust(justify)
                if len(pfx) >= justify:
                    s += f"\n{''.ljust(justify)}"
                s += f" {help}"
                return s

            for opt in self.options.items():
                if opt.required:
                    s += f" --{opt.name} {opt.name.upper()}"
                    oh = opt_help(f"--{opt.name}", param=f"{opt.name.upper()}", help=opt.help)
                    required_help += f"\n{oh}"
            for opt in self.options.items():
                if not opt.required:
                    s += f" [--{opt.name} {opt.name.upper()}]"
                    oh = opt_help(f"--{opt.name}", param=f"{opt.name.upper()}", help=opt.help)
                    optional_help += f"\n{oh}"

            if required_help:
                s += f"\n\nRequired arguments:{required_help}"
            if optional_help:
                s += f"\n\nOptional arguments:{optional_help}"
            
            return s

        def invoke(self, node_address:str, port:int, path_format:str, args:dict):
            path_dict = dict()
            params_dict = dict()
            kind_str = self.kind_to_str[self.kind]

            def get_value(opt_name:str):
                value = args.pop(opt_name)
                if type(value) is list:
                    if len(value) == 1:
                        value = value[0]
                    else:
                        value = ','.join(value)
                return value

            for opt in self.options.items():
                if opt.param_type == 'path':
                    try:
                        path_dict[opt.name] = get_value(opt.name)
                    except KeyError:
                        print(f"{self.command_name} {kind_str}: missing required value path argument '{opt.name}'")
                        return
                else:
                    try:
                        params_dict[opt.name] = get_value(opt.name)
                    except KeyError:
                        pass
            url = f"http://{node_address}:{port}/{path_format.format(**path_dict)}"
            log.debug(f"request('{kind_str}', url={url}, params={params_dict})")
            res = requests.request(kind_str, url=url, params=params_dict)
            print(f"{res.text}")

    # init Command
    def __init__(self, module_name:str, command_name:str):
        self.module_name = module_name
        self.name = command_name
        # name format is used for generting the command url
        # it may include positional path arguments like "my_module/my_command/{param}"
        self.name_format = f"{module_name}/{command_name}"
        self.methods = dict()
        log.debug(f"Created {self.__repr__()}")

    def __repr__(self):
        return f"ApiCommand(name={self.name}, methods={self.methods})"

    def __str__(self):
        s = f"{self.module_name}/{self.name}:"
        for _, method in self.methods.items():
            method_str = f"{method}"
            re.sub('\n', '\n    ', method_str)
            s += f"\n  {method_str}"
        return s

    def add_method(self, method:Method):
        self.methods[method.kind] = method

    def load_json(self, command_json:dict):
        log.debug(f"Loading: {json.dumps(command_json, indent=4)}")
        for operation_def in command_json["operations"]:
            if operation_def["method"].upper() == "GET":
                kind = ScyllaApiCommand.Method.GET
            elif operation_def["method"].upper() == "POST":
                kind = ScyllaApiCommand.Method.POST
            elif operation_def["method"].upper() == "DELETE":
                kind = ScyllaApiCommand.Method.DELETE
            else:
                log.warn(f"Operation not supported yet: {json.dumps(operation_def, indent=4)}")
                continue

            method = ScyllaApiCommand.Method(kind=kind, desc=operation_def["summary"], command_name=self.name)
            for param_def in operation_def["parameters"]:
                method.add_option(ScyllaApiOption(param_def["name"],
                    required=param_def.get("required", False),
                    param_type=param_def.get("paramType", 'query'),
                    allowed_values=param_def.get("enum", []),
                    help=param_def["description"]))
            self.add_method(method)

    def invoke(self, node_address:str, port:int, argv=[]):
        method_kind = None
        if len(argv) and argv[0] in self.Method.str_to_kind:
            method_kind = self.Method.str_to_kind[argv[0]]
            argv = argv[1:]
        if method_kind is None:
            if len(self.methods) == 1:
                method_kind = list(self.methods.keys())[0]
        elif not self.methods[method_kind]:
            print(f"{self.name}: {self.Method.kind_to_str[method_kind]} method is not supported")
            return

        log.debug(f"Invoking {self.name} {self.Method.kind_to_str[method_kind] if method_kind is not None else 'None'} {argv}")
        print_help = '-h' in argv or '--help' in argv
        if print_help:
            print(f"{self.name} API syntax:\n")
        kind_strings = []
        for kind, m in self.methods.items():
            kind_str = self.Method.kind_to_str[kind]
            kind_strings.append(kind_str)
            if not m.parser:
                m.generate_parser()
            if print_help and (method_kind is None or method_kind == kind):
                if len(kind_strings) > 1:
                    print('---')
                print(f"{m.get_help()}")
        if print_help:
            return
        if method_kind is None:
            print(f"{self.name}: request method not specified. Use one of {'|'.join(kind_strings)}.")
            return
        try:
            method = self.methods[method_kind]
        except KeyError:
            print(f"{self.name}: {method_kind} method is not supported")
            return
        args = vars(method.parser.parse_args(argv))
        # FIXME: check properly option format (e.g.)
        provided_options = set(args.keys())
        required_options = set(opt.name for opt in method.options.items() if opt.required)
        assert(required_options.issubset(provided_options))
        method.invoke(node_address=node_address, port=port, path_format=self.name_format, args=args)

class ScyllaApiModule:
    # init Module
    def __init__(self, name:str, desc:str='', commands:OrderedDict=None):
        self.desc = desc
        self.name = name
        self.commands = commands or OrderedDict()
        log.debug(f"Created {self.__repr__()}")

    def __repr__(self):
        return f"ApiModule(name={self.name}, desc={self.desc}, commands={self.commands})"

    def __str__(self):
        s = f"{self.name}: {self.desc}"
        for command_name in self.commands.keys():
            command = self.commands[command_name]
            if s:
                s += '\n'
            command_str = f"{command}"
            re.sub('\n', '\n    ', command_str)
            s += f"\n  {command_str}"
        return s

    def add_command(self, command:ScyllaApiCommand):
        self.commands.insert(command.name, command)

class ScyllaApi:
    default_address = 'localhost'
    default_port = 10000

    # init ScyllaApi
    def __init__(self):
        self.modules = OrderedDict()
        self.client = None

    def __repr__(self):
        return f"ScyllaApi(node_address={self.node_address}, port={self.port}, modules={self.modules})"

    def __str__(self):
        s = ''
        for module_name in self.modules.keys():
            module = self.modules[module_name]
            if s:
                s += '\n'
            s += f"{module}"
        return s

    def add_module(self, module:ScyllaApiModule):
        self.modules.insert(module.name, module)

    def load(self, node_address:str=default_address, port:int=default_port):
        self.client = ScyllaRestClient(host=node_address, port=port)

        # FIXME: handle service down, assert minimum version
        top_json = self.client.get_raw_api_json()
        for module_def in top_json["apis"]:
            # FIXME: handle service down, errors
            module_json = self.client.get_raw_api_json(f"{module_def['path']}/")
            module_path = module_def['path'].strip(' /')
            module = ScyllaApiModule(module_path, module_def['description'])
            for command_json in module_json["apis"]:
                command_path = command_json['path'].strip(' /')
                if command_path.startswith(module_path):
                    command_path = command_path[len(module_path)+1:]
                command = ScyllaApiCommand(module_name=module_path, command_name=command_path)
                command.load_json(command_json)
                module.add_command(command)
            self.add_module(module)
