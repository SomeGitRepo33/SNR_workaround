# SNR_ansible_workaround

Переделка https://github.com/ansible/ansible/blob/stable-2.9/lib/ansible/plugins/terminal/ios.py
для возможности работы с коммутаторами SNR, на которых пользователь не попадает сразу в enable_mode.
Циски позволяют выполнять команду terminal length 0 в непривилегированном режиме, тогда как SNR - нет.

Для использования - заменить оригинальный ansible/plugins/terminal/ios.py

При использовании ios.py теперь неободимо ВСЕГДА указывать ansible_become: yes и ansible_become_method: enable, соответственно у пользователя ДОЛЖНЫ быть права на переход в enable_mode.

Костыль до написания нормального плагина.
