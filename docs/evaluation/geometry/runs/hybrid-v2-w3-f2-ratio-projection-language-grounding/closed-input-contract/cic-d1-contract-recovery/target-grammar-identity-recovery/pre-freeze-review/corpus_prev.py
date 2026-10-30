"""Emulate df475f06 exactly on the HEAD tree (product diff df475f06..HEAD = these two hunks), then run the corpus sweep."""
import os, runpy, sys
sys.dont_write_bytecode = True
sys.path.insert(0, sys.argv[1]); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.simulation.geometry_functions import typed_fact_next as T
import mutplugin as MP
MP._mutate(T, '_validate_goal_target', [('valid = any(set(target) == set(a) for a in alternatives)',
    'valid = bool(set(target) & scopes) and any(set(a) <= scopes for a in alternatives)')])
T._validate_goal_identities = lambda p: None
runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'corpus_schema.py'), run_name='__main__')
