# -*- coding: utf-8 -*-
#
# Copyright (c) 2015, ParaTools, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# (1) Redistributions of source code must retain the above copyright notice,
#     this list of conditions and the following disclaimer.
# (2) Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions and the following disclaimer in the documentation
#     and/or other materials provided with the distribution.
# (3) Neither the name of ParaTools, Inc. nor the names of its contributors may
#     be used to endorse or promote products derived from this software without
#     specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
"""``tau target create`` subcommand."""

from tau import EXIT_SUCCESS
from tau.error import ConfigurationError
from tau.cli import arguments
from tau.cli.cli_view import CreateCommand
from tau.core import storage
from tau.core.mvc import UniqueAttributeError
from tau.core.target import Target
from tau.core.compiler import Compiler
from tau.cf.compiler import CompilerFamily, CompilerRole
from tau.cf.compiler.mpi import MpiCompilerFamily, MPI_CXX_ROLE, MPI_CC_ROLE, MPI_FC_ROLE
from tau.cf.compiler.installed import InstalledCompiler, InstalledCompilerFamily
from tau.cf.target import host


class TargetCreateCommand(CreateCommand):
    """``tau target create`` subcommand."""
    
    def parse_compiler_flags(self, args):
        """Parses host compiler flags out of the command line arguments.
         
        Args:
            args: Argument namespace containing command line arguments
             
        Returns:
            Dictionary of installed compilers by role keyword string.
             
        Raises:
            ConfigurationError: Invalid command line arguments specified
        """
        for family_attr, family_cls in [('host_family', CompilerFamily), ('mpi_family', MpiCompilerFamily)]:
            try:
                family_arg = getattr(args, family_attr)
            except AttributeError as err:
                # User didn't specify that argument, but that's OK
                self.logger.debug(err)
                continue
            else:
                delattr(args, family_attr)
            try:
                family_comps = InstalledCompilerFamily(family_cls(family_arg))
            except KeyError:
                self.parser.error("Invalid compiler family: %s" % family_arg)
            for comp in family_comps:
                self.logger.debug("args.%s=%r", comp.info.role.keyword, comp.absolute_path)
                setattr(args, comp.info.role.keyword, comp.absolute_path)
     
        compiler_keys = set(CompilerRole.keys())
        all_keys = set(args.__dict__.keys())
        given_keys = compiler_keys & all_keys
        missing_keys = compiler_keys - given_keys
        self.logger.debug("Given compilers: %s", given_keys)
        self.logger.debug("Missing compilers: %s", missing_keys)
         
        compilers = dict([(key, InstalledCompiler(getattr(args, key))) for key in given_keys])
        for key in missing_keys:
            try:
                compilers[key] = host.default_compiler(CompilerRole.find(key))
            except ConfigurationError as err:
                self.logger.debug(err)
    
        # Check that all required compilers were found
        for role in CompilerRole.tau_required():
            if role.keyword not in compilers:
                raise ConfigurationError("%s compiler could not be found" % role.language,
                                         "See 'compiler arguments' under `%s --help`" % COMMAND)
                
        # Probe MPI compilers to discover wrapper flags
        for args_attr, wrapped_attr in [('mpi_include_path', 'include_path'), 
                                        ('mpi_library_path', 'library_path'),
                                        ('mpi_libraries', 'libraries')]:
            if not hasattr(args, args_attr):
                probed = set()
                for role in MPI_CC_ROLE, MPI_CXX_ROLE, MPI_FC_ROLE:
                    try:
                        comp = compilers[role.keyword]
                    except KeyError:
                        self.logger.debug("Not probing %s: not found", role)
                    else:
                        probed.update(getattr(comp.wrapped, wrapped_attr))
                setattr(args, args_attr, list(probed))
    
        return compilers
    
    def construct_parser(self):
        parser = super(TargetCreateCommand, self).construct_parser()
        group = parser.get_group('compiler arguments')
        group.add_argument('--host-compilers',
                           help="select all host compilers automatically from the given family",
                           metavar='<family>',
                           dest='host_family',
                           default=host.preferred_compilers().name,
                           choices=CompilerFamily.family_names())
        group = parser.get_group('Message Passing Interface (MPI) arguments')
        group.add_argument('--mpi-compilers', 
                           help="select all MPI compilers automatically from the given family",
                           metavar='<family>',
                           dest='mpi_family',
                           default=host.preferred_mpi_compilers().name,
                           choices=MpiCompilerFamily.family_names())
        return parser
    
    def main(self, argv):
        args = self.parser.parse_args(args=argv)
        self.logger.debug('Arguments: %s', args)
        store = storage.CONTAINERS[getattr(args, arguments.STORAGE_LEVEL_FLAG)[0]]
        ctrl = self.controller(store)
        key_attr = ctrl.key_attribute
        key = getattr(args, key_attr)
        data = {attr: getattr(args, attr) for attr in ctrl.attributes if hasattr(args, attr)}

        compilers = self.parse_compiler_flags(args)
        self.logger.debug('Arguments after parsing compiler flags: %s', args)
    
        for keyword, comp in compilers.iteritems():
            self.logger.debug("%s=%s (%s)", keyword, comp.absolute_path, comp.info.short_descr)
            record = Compiler(store).register(comp)
            data[comp.info.role.keyword] = record.eid
    
        try:
            ctrl.create(data)
        except UniqueAttributeError:
            self.parser.error("A %s with %s='%s' already exists" % (self.model_name, key_attr, key))
        self.logger.info("Created a new %s-level %s: '%s'.", ctrl.storage.name, self.model_name, key)
        return EXIT_SUCCESS

COMMAND = TargetCreateCommand(Target, __name__)
