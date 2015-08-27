#"""
#@file
#@author John C. Linford (jlinford@paratools.com)
#@version 1.0
#
#@brief
#
# This file is part of TAU Commander
#
#@section COPYRIGHT
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
#"""

from tau import logger
from tau.cf.compiler import CompilerFamily, CompilerRole


LOGGER = logger.get_logger(__name__)


class MpiCompilerFamily(CompilerFamily):
    """Information about an MPI compiler family.
    
    Subclassing CompilerFamily creates a second database of compiler family 
    records and keep MPI compilers from mixing with host etc. compilers.
    """
    
    def __init__(self, *args, **kwargs):
        if 'show_wrapper_flags' not in kwargs:
            kwargs['show_wrapper_flags'] = ['-show']
        super(MpiCompilerFamily,self).__init__(*args, **kwargs)
    
    @classmethod
    def preferred(cls):
        from tau.cf.target import host
        return host.preferred_mpi_compilers()


MPI_CC_ROLE = CompilerRole('MPI_CC', 'MPI C')
MPI_CXX_ROLE = CompilerRole('MPI_CXX', 'MPI C++')
MPI_FC_ROLE = CompilerRole('MPI_FC', 'MPI Fortran')

SYSTEM_MPI_COMPILERS = MpiCompilerFamily('System')
SYSTEM_MPI_COMPILERS.add(MPI_CC_ROLE, 'mpicc')
SYSTEM_MPI_COMPILERS.add(MPI_CXX_ROLE, 'mpic++', 'mpicxx', 'mpiCC')
SYSTEM_MPI_COMPILERS.add(MPI_FC_ROLE, 'mpiftn', 'mpif90', 'mpif77')

INTEL_MPI_COMPILERS = MpiCompilerFamily('Intel')
INTEL_MPI_COMPILERS.add(MPI_CC_ROLE, 'mpiicc')
INTEL_MPI_COMPILERS.add(MPI_CXX_ROLE, 'mpiicpc')
INTEL_MPI_COMPILERS.add(MPI_FC_ROLE, 'mpiifort')

IBM_MPI_COMPILERS = MpiCompilerFamily('IBM')
IBM_MPI_COMPILERS.add(MPI_CC_ROLE, 'mpixlc')
IBM_MPI_COMPILERS.add(MPI_CXX_ROLE, 'mpixlc++', 'mpixlC')
IBM_MPI_COMPILERS.add(MPI_FC_ROLE, 'mpixlf77')

CRAY_MPI_COMPILERS = MpiCompilerFamily('Cray', show_wrapper_flags=['-craype-verbose'])
CRAY_MPI_COMPILERS.add(MPI_CC_ROLE, 'cc')
CRAY_MPI_COMPILERS.add(MPI_CXX_ROLE, 'CC')
CRAY_MPI_COMPILERS.add(MPI_FC_ROLE, 'ftn')
