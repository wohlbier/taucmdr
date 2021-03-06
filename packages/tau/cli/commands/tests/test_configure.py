# -*- coding: utf-8 -*-
#
# Copyright (c) 2016, ParaTools, Inc.
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

"""Test functions.

Functions used for unit tests of configure.py.
"""

from tau import tests
from tau.cli.commands.configure import COMMAND as configure_cmd
from tau.cf.storage.project import ProjectStorageError


class ConfigureTest(tests.TestCase):
    """Unit tests for `tau configure`"""

    def test_no_args(self):
        self.reset_project_storage(bare=True)
        stdout, stderr = self.assertCommandReturnValue(0, configure_cmd, [])
        self.assertFalse(stderr)
        self.assertIn("selected_project", stdout)

    def test_no_project(self):
        self.destroy_project_storage()
        self.assertRaises(ProjectStorageError, self.exec_command, cmd=configure_cmd, argv=['some_key'])

    def test_invalid_key(self):
        self.reset_project_storage(bare=True)
        stdout, stderr = self.assertNotCommandReturnValue(0, configure_cmd, ['invalid_key'])
        self.assertFalse(stdout)
        self.assertIn("Invalid key: invalid_key", stderr)

    def test_h_arg(self):
        self.reset_project_storage(project_name='proj1')
        stdout, _ = self.assertCommandReturnValue(0, configure_cmd, ['-h'])
        self.assertIn('Show this help message and exit', stdout)

    def test_help_arg(self):
        self.reset_project_storage(project_name='proj1')
        stdout, _ = self.assertCommandReturnValue(0, configure_cmd, ['--help'])
        self.assertIn('Show this help message and exit', stdout)
