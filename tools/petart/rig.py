"""Model rig: bones + boxes in Minecraft model space (pixels, Y down, front = -Z, ground at y=24).

The same data drives the Java LayerDefinition code, the UV layout, the painter and the preview renderer,
so what we review is exactly what the game draws.
"""
import math
from dataclasses import dataclass, field

# Face names follow the look of the face from outside (a skin-style "picture"):
#   top    = region (u+d, v)        w x d   (row 0 = back edge, last row = front edge)
#   bottom = region (u+d+w, v)      w x d
#   right  = region (u, v+d)        d x h   (WEST, the pet's right side; col 0 = back)
#   front  = region (u+d, v+d)      w x h   (NORTH; col 0 = pet's right side)
#   left   = region (u+d+w, v+d)    d x h   (EAST, the pet's left side; col 0 = front)
#   back   = region (u+2d+w, v+d)   w x h   (SOUTH; col 0 = pet's left side)
FACES = ('top', 'bottom', 'right', 'front', 'left', 'back')
JAVA_DIR = {'top': 'DOWN', 'bottom': 'UP', 'right': 'WEST', 'front': 'NORTH', 'left': 'EAST', 'back': 'SOUTH'}


@dataclass
class Cube:
    x: float
    y: float
    z: float
    w: int
    h: int
    d: int
    mat: str = 'base'
    name: str = ''
    inflate: float = 0.0
    faces: tuple = None          # subset of FACES that exist (None = all six)
    uv: tuple = None             # filled in by the packer

    def regions(self):
        """Texture rectangles (u, v, width, height) per face."""
        u, v = self.uv
        w, h, d = self.w, self.h, self.d
        return {
            'top': (u + d, v, w, d),
            'bottom': (u + d + w, v, w, d),
            'right': (u, v + d, d, h),
            'front': (u + d, v + d, w, h),
            'left': (u + d + w, v + d, d, h),
            'back': (u + 2 * d + w, v + d, w, h),
        }

    def has(self, face):
        return self.faces is None or face in self.faces

    def footprint(self):
        return 2 * (self.w + self.d), self.d + self.h


@dataclass
class Bone:
    name: str
    pivot: tuple = (0.0, 0.0, 0.0)
    rot: tuple = (0.0, 0.0, 0.0)      # degrees, applied Z*Y*X like ModelPart
    cubes: list = field(default_factory=list)
    children: list = field(default_factory=list)

    def add(self, *things):
        for t in things:
            (self.cubes if isinstance(t, Cube) else self.children).append(t)
        return self

    def walk(self):
        yield self
        for c in self.children:
            yield from c.walk()

    def find(self, name):
        for b in self.walk():
            if b.name == name:
                return b
        return None


def box(x, y, z, w, h, d, mat='base', name='', inflate=0.0, faces=None):
    return Cube(x, y, z, w, h, d, mat, name, inflate, faces)


# ----------------------------------------------------------------------------------------------
# UV packing (skyline)

def pack(roots, sizes=((64, 64), (128, 64), (128, 128), (256, 128))):
    cubes = [c for r in roots for b in r.walk() for c in b.cubes]
    order = sorted(cubes, key=lambda c: (-c.footprint()[1], -c.footprint()[0]))
    for tw, th in sizes:
        sky = [0] * tw
        ok = True
        placed = {}
        for c in order:
            fw, fh = c.footprint()
            fw, fh = max(fw, 1), max(fh, 1)
            best = None
            for u in range(0, tw - fw + 1):
                top = max(sky[u:u + fw])
                if top + fh <= th and (best is None or (top, u) < best[:2]):
                    best = (top, u)
            if best is None:
                ok = False
                break
            top, u = best
            placed[id(c)] = (u, top)
            for i in range(u, u + fw):
                sky[i] = top + fh
        if ok:
            for c in cubes:
                c.uv = placed[id(c)]
            return tw, th
    raise RuntimeError('model does not fit into 256x128')


# ----------------------------------------------------------------------------------------------
# Java code generation

def _f(v):
    s = ('%.4f' % v).rstrip('0').rstrip('.')
    if s in ('-0', ''):
        s = '0'
    return s + 'F'


def java_layer(method, roots, tex_w, tex_h):
    lines = [f'    public static LayerDefinition {method}() {{',
             '        MeshDefinition mesh = new MeshDefinition();',
             '        PartDefinition root = mesh.getRoot();']

    def emit(bone, parent_var, depth):
        var = 'p_' + bone.name
        parts = ['CubeListBuilder.create()']
        for c in bone.cubes:
            parts.append(f'.texOffs({c.uv[0]}, {c.uv[1]})')
            if c.faces is not None:
                dirs = ', '.join('Direction.' + JAVA_DIR[f] for f in c.faces)
                parts.append(f'.addBox({_f(c.x)}, {_f(c.y)}, {_f(c.z)}, {_f(c.w)}, {_f(c.h)}, {_f(c.d)}, EnumSet.of({dirs}))')
            elif c.inflate:
                parts.append(f'.addBox({_f(c.x)}, {_f(c.y)}, {_f(c.z)}, {_f(c.w)}, {_f(c.h)}, {_f(c.d)}, new CubeDeformation({_f(c.inflate)}))')
            else:
                parts.append(f'.addBox({_f(c.x)}, {_f(c.y)}, {_f(c.z)}, {_f(c.w)}, {_f(c.h)}, {_f(c.d)})')
        rx, ry, rz = (math.radians(a) for a in bone.rot)
        px, py, pz = bone.pivot
        pose = f'PartPose.offsetAndRotation({_f(px)}, {_f(py)}, {_f(pz)}, {_f(rx)}, {_f(ry)}, {_f(rz)})'
        builder = ('\n' + ' ' * 16).join(parts)
        lines.append(f'        PartDefinition {var} = {parent_var}.addOrReplaceChild("{bone.name}", {builder},\n                {pose});')
        for ch in bone.children:
            emit(ch, var, depth + 1)

    for r in roots:
        emit(r, 'root', 0)
    lines.append(f'        return LayerDefinition.create(mesh, {tex_w}, {tex_h});')
    lines.append('    }')
    return '\n'.join(lines)


# ----------------------------------------------------------------------------------------------
# Geometry for the preview renderer (mirrors ModelPart.Cube exactly)

def _rot_zyx(rx, ry, rz):
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)
    rxm = [[1, 0, 0], [0, cx, -sx], [0, sx, cx]]
    rym = [[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]
    rzm = [[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]
    return _mm(_mm(rzm, rym), rxm)


def _mm(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def _mv(m, v):
    return [sum(m[i][k] * v[k] for k in range(3)) for i in range(3)]


def quads(roots, pose=None, hidden=()):
    """World-ish quads in model units (pixels, still Y-down): list of (verts[4][3], uvs[4][2], normal)."""
    pose = pose or {}
    out = []

    def rec(bone, M, t):
        if bone.name in hidden:
            return
        px, py, pz = bone.pivot
        dx, dy, dz, drx, dry, drz = pose.get(bone.name, (0, 0, 0, 0, 0, 0))
        R = _rot_zyx(math.radians(bone.rot[0] + drx), math.radians(bone.rot[1] + dry), math.radians(bone.rot[2] + drz))
        tt = [t[i] + _mv(M, [px + dx, py + dy, pz + dz])[i] for i in range(3)]
        MM = _mm(M, R)
        for c in bone.cubes:
            g = c.inflate
            x0, y0, z0 = c.x - g, c.y - g, c.z - g
            x1, y1, z1 = c.x + c.w + g, c.y + c.h + g, c.z + c.d + g
            T0, T1, T2, T3 = (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)
            L0, L1, L2, L3 = (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)
            u, v = c.uv
            w, h, d = c.w, c.h, c.d
            u0, u1, u2, u22, u3, u4 = u, u + d, u + d + w, u + d + w + w, u + d + w + d, u + d + w + d + w
            v0, v1, v2 = v, v + d, v + d + h
            polys = {
                'top': ([L1, L0, T0, T1], u1, v0, u2, v1, (0, -1, 0)),
                'bottom': ([T2, T3, L3, L2], u2, v1, u22, v0, (0, 1, 0)),
                'right': ([T0, L0, L3, T3], u0, v1, u1, v2, (-1, 0, 0)),
                'front': ([T1, T0, T3, T2], u1, v1, u2, v2, (0, 0, -1)),
                'left': ([L1, T1, T2, L2], u2, v1, u3, v2, (1, 0, 0)),
                'back': ([L0, L1, L2, L3], u3, v1, u4, v2, (0, 0, 1)),
            }
            for f, (vs, a0, b0, a1, b1, n) in polys.items():
                if not c.has(f):
                    continue
                uvs = [(a1, b0), (a0, b0), (a0, b1), (a1, b1)]
                wv = [[tt[i] + _mv(MM, list(p))[i] for i in range(3)] for p in vs]
                out.append((wv, uvs, _mv(MM, list(n))))
        for ch in bone.children:
            rec(ch, MM, tt)

    for r in roots:
        rec(r, [[1, 0, 0], [0, 1, 0], [0, 0, 1]], [0, 0, 0])
    return out
