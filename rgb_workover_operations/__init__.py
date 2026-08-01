# -*- coding: utf-8 -*-
from . import models
from . import wizard


def pre_init_hook(env):
    from .hooks import pre_init_hook as _pre_init_hook
    _pre_init_hook(env)


def post_init_hook(env):
    from .hooks import post_init_hook as _post_init_hook
    _post_init_hook(env)
