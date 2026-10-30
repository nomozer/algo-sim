"""pytest plugin: apply ONE reviewer mutant (env REVIEW_MUTANT) to typed_fact_next in memory. Never writes product files."""
import inspect, os, textwrap


def _mutate(mod, name, pairs):
    src = textwrap.dedent(inspect.getsource(getattr(mod, name)))
    for a, b in pairs:
        assert a in src, (name, a)
        src = src.replace(a, b)
    ns = {}
    exec(compile(src, f'<mutant {name}>', 'exec'), mod.__dict__, ns)
    setattr(mod, name, ns[name])


def pytest_configure(config):
    m = os.environ.get('REVIEW_MUTANT')
    if not m:
        return
    from app.simulation.geometry_functions import typed_fact_next as T
    if m == 'M_raw_label':          # distinctness by bare label (drops binding/namespace resolution)
        _mutate(T, '_validate_goal_identities', [('[canonical_vertex_ref(p, ref, scope) for ref in refs]',
                                                  '[parse_qualified_ref(ref)[1] for ref in refs]')])
    elif m == 'M_segment_only':     # only checks the `segment` operand
        _mutate(T, '_validate_goal_identities', [('if GOAL_OPERAND_SHAPES[key].startswith("refs"):', 'if key == "segment":')])
    elif m == 'M_no_ambiguity':     # fallback silently picks one identity
        _mutate(T, 'canonical_vertex_ref', [('if len(identities) > 1:', 'if False:')])
    elif m == 'M_no_derived_parent_ns':   # derived namespace not mapped to its parent
        _mutate(T, 'canonical_vertex_ref', [('ns = parents.get(ns, ns)', 'ns = ns')])
    elif m == 'M_no_derived_parent_scope':  # derived scope not mapped to its parent
        _mutate(T, 'canonical_vertex_ref', [('parents.get(scope, scope)', 'scope')])
    elif m == 'M_identity_before_scope':  # ordering: identity check before S1-S11 declared-scope policy
        orig_ids, orig_scope = T._validate_goal_identities, T._validate_declared_solid_scope
        def scope_first_ids(p, known):
            orig_ids(p)
            return orig_scope(p, known)
        T._validate_declared_solid_scope = scope_first_ids
        T._validate_goal_identities = lambda p: None
    elif m == 'M_f1_superset':      # F1 scope-only branch accepts supersets of a registered alternative
        _mutate(T, '_validate_goal_target', [('valid = any(set(target) == set(a) for a in alternatives)',
                                              'valid = any(set(target) >= set(a) for a in alternatives)')])
    elif m == 'M_f1_volume_solid_id_everywhere':  # solid_id treated as alias of solid in the scope-only branch
        _mutate(T, '_validate_goal_target', [('valid = any(set(target) == set(a) for a in alternatives)',
                                              'valid = any(set(target) == set(a) or set(target) == {"solid_id"} and ["solid"] in alternatives for a in alternatives)')])
    elif m == 'M_unscoped_only':    # skip identity check when the measurement is scoped
        _mutate(T, '_validate_goal_identities', [('scope = measurement_scope(p, goal)',
                                                  'scope = measurement_scope(p, goal)\n        if scope is not None: continue')])
    else:
        raise RuntimeError('unknown mutant ' + m)
    print('REVIEW_MUTANT applied:', m)
