"""This module is modified ios.py from ansible terminal plugins.
    I modified it because SNR switches do not allow set terminal params
    in unprivileged mode, so ios.py fails, when you connecting in that one.
    It's like  simple workaround.
    !!!ATENTION!!!
    Now you MUST set 'ansible_become: yes' and 'ansible_become_method: enable' in your
    connection variables AND you user MUST have rights to enable privileged mode.
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import re

from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils._text import to_text, to_bytes
from ansible.plugins.terminal import TerminalBase
from ansible.utils.display import Display

display = Display()

def _prepare_shell(term_obj):
    """Moved this code from 'on_open_shell' method to use this plugin with SNR NOS."""
    try:
        term_obj._exec_cli_command(b'terminal length 0')
    except AnsibleConnectionFailure:
        raise AnsibleConnectionFailure('unable to set terminal parameters')

    try:
        term_obj._exec_cli_command(b'terminal width 512')
        try:
            term_obj._exec_cli_command(b'terminal width 0')
        except AnsibleConnectionFailure:
            pass
    except AnsibleConnectionFailure:
        display.display('WARNING: Unable to set terminal width, command responses may be truncated')


class TerminalModule(TerminalBase):

    terminal_stdout_re = [
        re.compile(br"[\r\n]?[\w\+\-\.:\/\[\]]+(?:\([^\)]+\)){0,3}(?:[>#]) ?$")
    ]

    terminal_stderr_re = [
        re.compile(br"% ?Error"),
        # re.compile(br"^% \w+", re.M),
        re.compile(br"% ?Bad secret"),
        re.compile(br"[\r\n%] Bad passwords"),
        re.compile(br"invalid input", re.I),
        re.compile(br"(?:incomplete|ambiguous) command", re.I),
        re.compile(br"connection timed out", re.I),
        re.compile(br"[^\r\n]+ not found"),
        re.compile(br"'[^']' +returned error code: ?\d+"),
        re.compile(br"Bad mask", re.I),
        re.compile(br"% ?(\S+) ?overlaps with ?(\S+)", re.I),
        re.compile(br"[%\S] ?Error: ?[\s]+", re.I),
        re.compile(br"[%\S] ?Informational: ?[\s]+", re.I),
        re.compile(br"Command authorization failed")
    ]

    def on_open_shell(self):
        """It's dummy now"""
        pass

    def on_become(self, passwd=None):
        if self._get_prompt().endswith(b'#'):
            _prepare_shell(self)
            return

        cmd = {u'command': u'enable'}
        if passwd:
            # Note: python-3.5 cannot combine u"" and r"" together.  Thus make
            # an r string and use to_text to ensure it's text on both py2 and py3.
            cmd[u'prompt'] = to_text(r"[\r\n](?:.*)?[Pp]assword: ?$", errors='surrogate_or_strict')
            cmd[u'answer'] = passwd
            cmd[u'prompt_retry_check'] = True
        try:
            self._exec_cli_command(to_bytes(json.dumps(cmd), errors='surrogate_or_strict'))
            prompt = self._get_prompt()
            if prompt is None or not prompt.endswith(b'#'):
                raise AnsibleConnectionFailure('failed to elevate privilege to enable mode still at prompt [%s]' % prompt)
        except AnsibleConnectionFailure as e:
            prompt = self._get_prompt()
            raise AnsibleConnectionFailure('unable to elevate privilege to enable mode, at prompt [%s] with error: %s' % (prompt, e.message))
        _prepare_shell(self)

    def on_unbecome(self):
        prompt = self._get_prompt()
        if prompt is None:
            # if prompt is None most likely the terminal is hung up at a prompt
            return

        if b'(config' in prompt:
            self._exec_cli_command(b'end')
            self._exec_cli_command(b'disable')

        elif prompt.endswith(b'#'):
            self._exec_cli_command(b'disable')
