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
"""Binutils software installation management.

GNU binutils provildes BFD, which TAU uses for symbol resolution during
sampling, compiler-based instrumentation, and other measurement approaches.
"""

import os
import sys
import glob
import shutil
import fileinput
from tau import logger, util
from tau.error import ConfigurationError
from tau.cf.target import DARWIN_OS, IBM_BGP_ARCH, IBM_BGQ_ARCH, IBM64_ARCH, INTEL_KNC_ARCH
from tau.cf.software import SoftwarePackageError
from tau.cf.software.installation import AutotoolsInstallation
from tau.cf.compiler.host import CC, CXX, PGI, GNU


LOGGER = logger.get_logger(__name__)
 
REPOS = {None: 'http://www.cs.uoregon.edu/research/paracomp/tau/tauprofile/dist/binutils-2.23.2.tar.gz'}

LIBRARIES = {None: ['libbfd.a']}


class BinutilsInstallation(AutotoolsInstallation):
    """Encapsulates a GNU binutils installation."""
    
    def __init__(self, sources, target_arch, target_os, compilers):
        # binutils can't be built with PGI compilers so substitute GNU compilers instead
        if compilers[CC].unwrap().info.family is PGI:
            try:
                gnu_compilers = GNU.installation()
            except ConfigurationError:
                raise SoftwarePackageError("GNU compilers (required to build binutils) could not be found.")
            compilers = compilers.modify(Host_CC=gnu_compilers[CC], Host_CXX=gnu_compilers[CXX])
        super(BinutilsInstallation, self).__init__('binutils', 'GNU Binutils', sources, 
                                                   target_arch, target_os, compilers, REPOS, None, LIBRARIES, None)

    def configure(self, flags, env):
        flags.extend(['--disable-nls', '--disable-werror'])
        for var in 'CPP', 'CC', 'CXX', 'FC', 'F77', 'F90':
            env[var] = None
        if self.target_os is DARWIN_OS:
            flags.append('CFLAGS=-Wno-error=unused-value -Wno-error=deprecated-declarations -fPIC')
            flags.append('CXXFLAGS=-Wno-error=unused-value -Wno-error=deprecated-declarations -fPIC')
        else:
            flags.append('CFLAGS=-fPIC')
            flags.append('CXXFLAGS=-fPIC')
        if self.target_arch is IBM_BGP_ARCH:
            flags.append('CC=/bgsys/drivers/ppcfloor/gnu-linux/bin/powerpc-bgp-linux-gcc')
            flags.append('CXX=/bgsys/drivers/ppcfloor/gnu-linux/bin/powerpc-bgp-linux-g++')
        elif self.target_arch is IBM_BGQ_ARCH:
            flags.append('CC=/bgsys/drivers/ppcfloor/gnu-linux/bin/powerpc64-bgq-linux-gcc')
            flags.append('CXX=/bgsys/drivers/ppcfloor/gnu-linux/bin/powerpc64-bgq-linux-g++')
        elif self.target_arch is IBM64_ARCH:
            flags.append('--disable-largefile')
        elif self.target_arch is INTEL_KNC_ARCH:
            k1om_ar = util.which('x86_64-k1om-linux-ar')
            if not k1om_ar:
                for path in glob.glob('/usr/linux-k1om-*'):
                    k1om_ar = util.which(os.path.join(path, 'bin', 'x86_64-k1om-linux-ar'))
                    if k1om_ar:
                        break
                else:
                    raise ConfigurationError("Cannot find KNC native compilers in /usr/linux-k1om-*")
            env['PATH'] = os.pathsep.join([os.path.dirname(k1om_ar), env.get('PATH', os.environ['PATH'])])
            flags.append('--host=x86_64-k1om-linux')
        return super(BinutilsInstallation, self).configure(flags, env)

    def make_install(self, flags, env, parallel=False):
        super(BinutilsInstallation, self).make_install(flags, env, parallel)

        LOGGER.debug("Copying missing BFD headers")
        for hdr in glob.glob(os.path.join(self.src_prefix, 'bfd', '*.h')):
            shutil.copy(hdr, self.include_path)
        for hdr in glob.glob(os.path.join(self.src_prefix, 'include', '*')):
            try:
                shutil.copy(hdr, self.include_path)
            except IOError:
                dst = os.path.join(self.include_path, os.path.basename(hdr))
                shutil.copytree(hdr, dst)

        LOGGER.debug("Copying missing libiberty libraries")
        shutil.copy(os.path.join(self.src_prefix, 'libiberty', 'libiberty.a'), self.lib_path)
        shutil.copy(os.path.join(self.src_prefix, 'opcodes', 'libopcodes.a'), self.lib_path)

        LOGGER.debug("Fixing BFD header")
        for line in fileinput.input(os.path.join(self.include_path, 'bfd.h'), inplace=1):
            # fileinput.input with inplace=1 redirects stdout to the input file ... freaky
            sys.stdout.write(line.replace('#if !defined PACKAGE && !defined PACKAGE_VERSION', '#if 0'))

    def compiletime_config(self, opts=None, env=None):
        """Configure compilation environment to use this software package. 

        Don't put `self.bin_path` in PATH since this offends ``ld`` on some systems.
        
        Args:
            opts (list): Optional list of command line options.
            env (dict): Optional dictionary of environment variables.
            
        Returns: 
            tuple: opts, env updated for the new environment.
        """
        opts = list(opts) if opts else []
        env = dict(env) if env else dict(os.environ)
        return list(set(opts)), env

    def runtime_config(self, opts=None, env=None):
        """Configure runtime environment to use this software package.
        
        Don't put `self.bin_path` in PATH since this offends ``ld`` on some systems
        but do put `self.lib_path` in LD_LIBRARY_PATH.
        
        Args:
            opts (list): Optional list of command line options.
            env (dict): Optional dictionary of environment variables.
            
        Returns: 
            tuple: opts, env updated for the new environment.
        """
        opts = list(opts) if opts else []
        env = dict(env) if env else dict(os.environ)
        if os.path.isdir(self.lib_path):
            if sys.platform == 'darwin':
                library_path = 'DYLD_LIBRARY_PATH'
            else:
                library_path = 'LD_LIBRARY_PATH'   
            try:
                env[library_path] = os.pathsep.join([self.lib_path, env[library_path]])
            except KeyError:
                env[library_path] = self.lib_path
        return list(set(opts)), env

