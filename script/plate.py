import math
from itertools import cycle

class Sketch():

    def __init__(self, plane):
        self.curves = List[ITrimmedCurve]()
        self.plane = plane

    def _add_curve(self, curve):
        self.curves.Add(curve)

    @staticmethod
    def point((x, y, z)):
        return Point.Create(MM(x),MM(y),MM(z))

    @staticmethod
    def direction(x, y, z):
        return Direction.Create(x, y, z)

    def frame(self, (x, y, z), dir1, dir2):
        return Frame.Create(self.point((x, y, z)), dir1, dir2)

    def line(self, dot1, dot2):
        result = CurveSegment.Create(self.point(dot1), self.point(dot2))
        self._add_curve(result)

    def circle(self, frame, radius, start=0, end=360):
        interval = Interval.Create(DEG(start), DEG(end))
        result = CurveSegment.Create(Circle.Create(frame, MM(radius)), interval)
        self._add_curve(result)

    def polygon(self, *args, **kwargs):
        for i in range(len(args) - 1):
            self.line(args[i], args[i + 1])
        if kwargs.get('close'):
            self.line(args[-1], args[0])

    def finish(self):
        return PlanarBody.Create(self.plane, self.curves).CreatedBody

def point((x, y, z)):
    return Point.Create(MM(x), MM(y), MM(z))

def direction((x, y, z)):
    return Direction.Create(x, y, z)

def line(dot1, dot2):
    return SketchLine.Create(point(dot1), point(dot2))

def plane(dot, normal):
    DatumPlaneCreator.Create(point(dot), normal, True)

def select(item):
    return Selection.Create(item)

def rotate(face, axis, angle):
    options = RevolveFaceOptions()
    options.ExtrudeType = ExtrudeType.ForceIndependent
    RevolveFaces.Execute(face, axis, DEG(angle), options)

def extrude(face, direction, length, merge=False):
    options = ExtrudeFaceOptions()
    if merge:
        options.ExtrudeType = ExtrudeType.Add
    else:
        options.ExtrudeType = ExtrudeType.ForceIndependent
    ExtrudeFaces.Execute(select(face), direction, MM(length), options)

def sweep(face, curve):
    options = SweepCommandOptions()
    options.ExtrudeType = ExtrudeType.ForceIndependent
    options.Select = True
    Sweep.Execute(face, curve, options)

def delete(*args):
    for item in args:
        if item:
            Delete.Execute(select(item))

def split_by_plane(body, cutter):
    SplitBody.ByCutter(select(body), select(cutter))

def split_by_face(body, cutter):
    SplitBody.ByCutter(select(body), select(cutter), True)

def merge_bodies(bodies):
    result = Combine.Merge(select(bodies))

def share_topology(tolerance=.1):
    options = ShareTopologyOptions()
    options.Tolerance = MM(tolerance)
    ShareTopology.FindAndFix(options)

def end():
    ViewHelper.ZoomToEntity()

def save(name):
    path = 'C:\\users\\frenc\\yandexdisk\\ans\\geo\\{}.scdoc'.format(name)
    options = ExportOptions.Create()
    DocumentSave.Execute(path, options)

def named_selection(name, items):
    select = Selection.Create(items)
    NamedSelection.Create(select, Selection.Empty())
    NamedSelection.Rename('Группа1', name)

def named_selection_auto(name, items, condition):
    temp = []
    for item in items:
        if condition(item):
            temp.append(item)
    named_selection(name, temp)
    return temp

# parameters
# -----------------------------------------------
RTOL = 1e-6

height = 30
width = 20
delta = .2

pitch = .5
gamma = math.radians(30)

pitchx = pitch / math.sin(gamma)
pitchy = pitch / math.cos(gamma)

ascent = 2 * delta

GetRootPart().SetName('plate')
delete(GetRootPart().Bodies, GetRootPart().DatumPlanes, GetRootPart().Curves, GetRootPart().Components)

# -----------------------------------------------
def coord_gen():
    ys = [0, delta, delta + ascent, ascent, ascent, delta + ascent, delta, 0]
    for item in cycle(ys):
        yield item
    
nx = int(math.ceil(width / pitchx))
ny = int(math.ceil(height / pitchy))

coords = coord_gen()

for i in range(nx):
    sketch = Sketch(Plane.PlaneZX)
    sketch.polygon(
        (i * pitchx, 0, next(coords)), 
        (i * pitchx, 0, next(coords)), 
        ((i + 1) * pitchx, 0, next(coords)), 
        ((i + 1) * pitchx, 0, next(coords)), close=True)
    sketch.finish()

coords = coord_gen()

for i in range(ny):
    sketch = Sketch(Plane.PlaneYZ)
    sketch.polygon(
        (0, i * pitchy, next(coords)),
        (0, i * pitchy, next(coords)),
        (0, (i + 1) * pitchy, next(coords)),
        (0, (i + 1) * pitchy, next(coords)), close=True)
    sketch.finish()

vec = direction((1, math.tan(gamma), 0))

for body in GetRootPart().Bodies[:nx]:
    extrude(body.Faces[0], vec, width/math.cos(gamma))

for body in GetRootPart().Bodies[:ny]:
    extrude(body.Faces[0], vec, width/math.cos(gamma))

merge_bodies(GetRootPart().Bodies)

plane((width, 0, 0), Direction.DirX)
plane((0, height, 0), Direction.DirY)

split_by_plane(GetRootPart().Bodies[0], GetRootPart().DatumPlanes[0])
split_by_plane(GetRootPart().Bodies[0], GetRootPart().DatumPlanes[1])

delete(GetRootPart().Bodies[1], GetRootPart().Bodies[2], GetRootPart().DatumPlanes)

# make tube cuts
# -----------------------------------------------
def tube_embed(plate, dot, r1, r2):
    sketch = Sketch(Plane.PlaneXY)
    frame = sketch.frame(dot, Direction.DirX, Direction.DirY)
    sketch.circle(frame, r1)
    sketch.circle(frame, r2)
    sketch.finish()

    extrude(GetRootPart().Bodies[-1].Faces[0], Direction.DirZ, delta + ascent)
    cutter = GetRootPart().Bodies[-1]

    split_by_face(plate, cutter.Faces[0])
    split_by_face(plate, cutter.Faces[1])

    delete(cutter)

r1 = 2.5
r2 = 3.

tube_embed(GetRootPart().Bodies[0], (5, 5, 0), r1, r2)
tube_embed(GetRootPart().Bodies[-2], (15, 5, 0), r1, r2)
tube_embed(GetRootPart().Bodies[-2], (5, 15, 0), r1, r2)
tube_embed(GetRootPart().Bodies[-2], (15, 15, 0), r1, r2)
tube_embed(GetRootPart().Bodies[-2], (10, 25, 0), r1, r2)

# name everything
# -----------------------------------------------
(AIR1, AIR2, TUB1, AIR3, TUB2, 
 AIR4, TUB3, AIR5, TUB4, PLT0, TUB5) = GetRootPart().Bodies

PLT0.Name = 'PLT0'
AIR1.Name = 'AIR1'
AIR2.Name = 'AIR2'
AIR3.Name = 'AIR3'
AIR4.Name = 'AIR4'
AIR5.Name = 'AIR5'
TUB1.Name = 'TUB1'
TUB2.Name = 'TUB2'
TUB3.Name = 'TUB3'
TUB4.Name = 'TUB4'
TUB5.Name = 'TUB5'

# create named selections
# -----------------------------------------------
AIR_Faces = AIR1.Faces + AIR2.Faces + AIR3.Faces + AIR4.Faces + AIR5.Faces
TUB_Faces = TUB1.Faces + TUB2.Faces + TUB3.Faces + TUB4.Faces + TUB5.Faces

face_up = lambda x: x.GetFaceNormal(0, 0).Z > 0
face_dn = lambda x: x.GetFaceNormal(0, 0).Z < 0
face_0 = lambda x: x.GetFaceNormal(0, 0).Z == 0
face_neq = lambda x, y: abs(x - y)/y > RTOL

named_selection_auto('air-up', AIR_Faces, face_up)
named_selection_auto('air-dn', AIR_Faces, face_dn)
named_selection_auto('tub-up', TUB_Faces, face_up)
named_selection_auto('tub-dn', TUB_Faces, face_dn)
named_selection_auto('plt-up', PLT0.Faces, face_up)
named_selection_auto('plt-dn', PLT0.Faces, face_dn)

faces = named_selection_auto('air-rnd', AIR_Faces, face_0)
area = faces[0].Area
faces = named_selection_auto('tub-rnd', TUB_Faces, lambda x: face_0(x) and face_neq(x.Area, area))
area = faces[0].Area
named_selection_auto('plt-rnd', PLT0.Faces, lambda x: face_0(x) and face_neq(x.Area, area))

share_topology()
end()
