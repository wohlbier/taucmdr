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
"""``tau trial delete`` subcommand."""

from tau import logger, cli
from tau.cli import arguments
from tau.error import ConfigurationError
from tau.model.experiment import Experiment
from tau.model.trial import Trial


LOGGER = logger.get_logger(__name__)

COMMAND = cli.get_command(__name__)

SHORT_DESCRIPTION = "Delete experiment trials."

HELP = """
'%(command)s' page to be written.
""" % {'command': COMMAND}


def parser():
    """Construct a command line argument parser.
    
    Constructing the parser may cause a lot of imports as :py:mod:`tau.cli` is explored.
    To avoid possible circular imports we defer parser creation until afer all
    modules are imported, hence this function.  The parser instance is maintained as
    an attribute of the function, making it something like a C++ function static variable.
    """
    if not hasattr(parser, 'inst'):
        usage_head = "%s <trial_number> [arguments]" % COMMAND
        parser.inst = arguments.get_parser(prog=COMMAND,
                                      usage=usage_head,
                                      description=SHORT_DESCRIPTION)
        parser.inst.add_argument('number', 
                            help="Number of the trial to delete",
                            metavar='<trial_number>')
                                     
    return parser.inst


def main(argv):
    """Subcommand program entry point.
    
    Args:
        argv (:py:class:`list`): Command line arguments.
        
    Returns:
        int: Process return code: non-zero if a problem occurred, 0 otherwise
    """
    args = parser().parse_args(args=argv)
    LOGGER.debug('Arguments: %s', args)

    selection = Experiment.get_selected()
    if not selection:
        raise ConfigurationError("No experiment configured.", "See `tau project select`")

    try:
        number = int(args.number)
    except ValueError:
        parser.inst.error("Invalid trial number: %s" % args.number)
    fields = {'experiment': selection.eid, 'number': number}
    if not Trial.exists(fields):
        parser.inst.error("No trial number %s in the current experiment.  "
                     "See `tau trial list` to see all trial numbers." % number)
    Trial.delete(fields)
    LOGGER.info('Deleted trial %s', number)

    return cli.execute_command(['trial', 'list'], [])