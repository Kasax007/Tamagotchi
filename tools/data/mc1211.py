"""The Minecraft 1.21.1 target of the data generators (branch port/1.21.1).

tools/sprites/build.py and tools/data/gen_data.py write the 26.x formats. gen_data.py ends by calling convert(), which
turns everything into what 1.21.1 reads; it can also run on its own:

    python3 tools/data/mc1211.py

What changes for 1.21.1:
* recipes: ingredients are objects ({"item": ...} / {"tag": ...}), not plain strings
* recipe advancements: the recipe_unlocked condition is "recipe", not "recipes"
* loot tables: "conditions" / "functions" lists with "condition" / "function" keys (26.x: "condition" / "modifier")
* advancement entity predicates: {"type": ...} (26.x: {"minecraft:entity_type": ...})
* item models: 1.21.1 has no assets/<ns>/items/ definitions. Each one becomes models/item/<id>.json:
  - a plain model reference becomes a child model ({"parent": ...});
  - a select on the block_state colour (dyed bed, basket, egg lamp, portrait) becomes the plain block model, the
    colour comes from the item colour provider in TamagotchiClient;
  - a select on display_context (pager, laser pointer) keeps the flat inventory model, the 3D one is swapped in by
    ItemRendererMixin outside the inventory;
  - a select on custom_model_data strings (the Tama Egg) becomes "overrides" on custom_model_data 1..10
    (TamaEggItem.modelData: the pet's place in PetSpecies);
  - the plush special models become builtin/entity models drawn by PlushItemRenderer
* entity type tag minecraft:can_breathe_under_water for the water-breathing pets (LivingEntity.canBreatheUnderwater is
  final in 1.21.1)
The converter only touches files that are still in the 26.x format, so running it twice changes nothing.
"""
import json
import os
import shutil

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
ASSETS = os.path.join(REPO, 'src/main/resources/assets/tamagotchi')
DATA_ROOT = os.path.join(REPO, 'src/main/resources/data')
DATA = os.path.join(DATA_ROOT, 'tamagotchi')
NS = 'tamagotchi:'

# PetSpecies order: the Tama Egg's custom_model_data is the place in this list, starting at 1
SPECIES = ['desert_dragon', 'jungle_dragon', 'tide_dragon', 'frost_penguin', 'ember_pup', 'sculk_wisp', 'void_kitten',
           'pebble_golem', 'hex_toad', 'mimic']
WATER_BREATHERS = ['tide_dragon', 'mimic']


def _read(path):
    with open(path) as f:
        return json.load(f)


def _write(path, body):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(body, f, indent=2)


def _files(folder):
    for root, _, names in os.walk(folder):
        for n in sorted(names):
            if n.endswith('.json'):
                yield os.path.join(root, n)


# ------------------------------------------------------------------ data

def ingredient(i):
    if isinstance(i, str):
        return {'tag': i[1:]} if i.startswith('#') else {'item': i}
    if isinstance(i, list):
        return [ingredient(x) for x in i]
    return i


def recipe(body):
    out = dict(body)
    if out.get('type') == 'minecraft:crafting_shaped':
        out['key'] = {k: ingredient(v) for k, v in out['key'].items()}
    elif out.get('type') == 'minecraft:crafting_shapeless':
        out['ingredients'] = [ingredient(v) for v in out['ingredients']]
    out.setdefault('category', 'misc')
    return out


def _predicates(x):
    """Advancements: {"minecraft:entity_type": T} -> {"type": T}, anywhere."""
    if isinstance(x, dict):
        y = {}
        for k, v in x.items():
            if k == 'minecraft:entity_type':
                y['type'] = v
            else:
                y[k] = _predicates(v)
        return y
    if isinstance(x, list):
        return [_predicates(v) for v in x]
    return x


def advancement(body):
    out = _predicates(body)
    for c in out.get('criteria', {}).values():
        cond = c.get('conditions', {})
        if c.get('trigger') == 'minecraft:recipe_unlocked' and 'recipes' in cond:
            cond['recipe'] = cond.pop('recipes')
    return out


def _loot_fn(m):
    m = dict(m)
    m['function'] = m.pop('type')
    return m


def _loot_cond(c):
    c = dict(c)
    c['condition'] = c.pop('type')
    return c


def loot(body):
    out = dict(body)
    pools = []
    for pool in out.get('pools', []):
        pool = dict(pool)
        if 'condition' in pool:
            cond = pool.pop('condition')
            pool['conditions'] = [_loot_cond(c) for c in (cond if isinstance(cond, list) else [cond])]
        entries = []
        for e in pool.get('entries', []):
            e = dict(e)
            if 'modifier' in e:
                mods = e.pop('modifier')
                e['functions'] = [_loot_fn(m) for m in (mods if isinstance(mods, list) else [mods])]
            entries.append(e)
        pool['entries'] = entries
        pools.append(pool)
    out['pools'] = pools
    return out


def convert_data():
    n = 0
    for f in _files(os.path.join(DATA, 'recipe')):
        b = _read(f)
        c = recipe(b)
        if c != b:
            _write(f, c)
            n += 1
    for f in _files(os.path.join(DATA, 'advancement')):
        b = _read(f)
        c = advancement(b)
        if c != b:
            _write(f, c)
            n += 1
    for f in _files(os.path.join(DATA, 'loot_table')):
        b = _read(f)
        c = loot(b)
        if c != b:
            _write(f, c)
            n += 1
    _write(os.path.join(DATA_ROOT, 'minecraft/tags/entity_type/can_breathe_under_water.json'),
           {'replace': False, 'values': [NS + p for p in WATER_BREATHERS]})
    return n


# ------------------------------------------------------------------ item models

def _plain(model):
    """The model a (possibly nested) 26.x item model resolves to by default."""
    t = model['type'].split(':')[-1]
    if t == 'model':
        return model['model']
    if t == 'select':
        if model.get('property', '').endswith('display_context'):
            for case in model['cases']:
                when = case['when'] if isinstance(case['when'], list) else [case['when']]
                if 'gui' in when:
                    return _plain(case['model'])
        return _plain(model['fallback'])
    if t == 'condition':
        return _plain(model['on_false'])
    raise ValueError('no plain model in ' + t)


def item_model(item, definition):
    """models/item/<item>.json for one 26.x item definition, or None when that file is already the right one."""
    m = definition['model']
    t = m['type'].split(':')[-1]
    if t == 'special':
        base = m.get('base', NS + 'item/template_plush')
        return {'parent': base}
    if t == 'select' and m.get('property', '').endswith('custom_model_data'):
        overrides = []
        for case in m['cases']:
            if case['when'] in SPECIES:
                overrides.append({'predicate': {'custom_model_data': SPECIES.index(case['when']) + 1}, 'model': _plain(case['model'])})
        overrides.sort(key=lambda o: o['predicate']['custom_model_data'])
        return {'parent': _plain(m['fallback']), 'overrides': overrides}
    target = _plain(m)
    if target == NS + 'item/' + item:
        return None
    return {'parent': target}


def convert_items():
    folder = os.path.join(ASSETS, 'items')
    n = 0
    if os.path.isdir(folder):
        for f in _files(folder):
            item = os.path.basename(f)[:-5]
            out = item_model(item, _read(f))
            if out is not None:
                _write(os.path.join(ASSETS, 'models/item', item + '.json'), out)
                n += 1
        shutil.rmtree(folder)
    # the plush template is drawn by code: builtin/entity keeps its display transforms
    tpl = os.path.join(ASSETS, 'models/item/template_plush.json')
    if os.path.exists(tpl):
        body = _read(tpl)
        if body.get('parent') != 'minecraft:builtin/entity':
            body = {'parent': 'minecraft:builtin/entity', **{k: v for k, v in body.items() if k != 'parent'}}
            _write(tpl, body)
    return n


def convert():
    d = convert_data()
    i = convert_items()
    print(f'1.21.1 target: {d} data files and {i} item models converted')


if __name__ == '__main__':
    convert()
