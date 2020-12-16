import math

''' -------------------------------------------------------
sketching 2D operations
------------------------------------------------------- '''
class Sketch():

    def __init__(self, plane):
        self.curves = List[ITrimmedCurve]()
        self.plane = plane

    def line(self, (x1, y1, z1), (x2, y2, z2)):
        pt1 = Point.Create(x1, y1, z1)
        pt2 = Point.Create(x2, y2, z2)
        result = CurveSegment.Create(pt1, pt2)
        self.curves.Add(result)

    def polygon(self, *args):
        for i in range(len(args) - 1):
            self.line(args[i], args[i + 1])
        self.line(args[-1], args[0])

    def circle(self, frame, radius, start=0, end=360):
        interval = Interval.Create(DEG(start), DEG(end))
        result = CurveSegment.Create(Circle.Create(frame, radius), interval)
        self.curves.Add(result)

    def finish(self):
        return PlanarBody.Create(self.plane, self.curves).CreatedBody.Faces[0]

''' -------------------------------------------------------
primitives
------------------------------------------------------- '''
def point((x, y, z)):
    return Point.Create(x, y, z)

def direction((x, y, z)):
    return Direction.Create(x, y, z)

def line(dot, vec):
    return Line.Create(point(dot), direction(vec))

def frame(dot, dir1, dir2):
    return Frame.Create(point(dot), dir1, dir2)

def plane(dot, dir1, dir2):
    return Plane.Create(frame(dot, dir1, dir2))

def datum_line(dot, vec, name='default'):
    DatumLine.Create(GetRootPart(), name, line(dot, vec))
    return GetRootPart().DatumLines[-1]

def datum_plane(dot, dir1, dir2, name='default'):
    DatumPlane.Create(GetRootPart(), name, 
                      plane(dot, dir1, dir2))
    return GetRootPart().DatumPlanes[-1]

def select(item):
    return Selection.Create(item)

''' -------------------------------------------------------
manipulating operations
------------------------------------------------------- '''
def revolve(face, axis, angle=DEG(360), merge=False):
    options = RevolveFaceOptions()
    options.ExtrudeType = ExtrudeType.ForceIndependent
    if merge:
        options.ExtrudeType = ExtrudeType.Add
    else:
        options.ExtrudeType = ExtrudeType.ForceIndependent
    RevolveFaces.Execute(select(face), axis, angle, 
                         options)

def extrude(face, direction, length, merge=False):
    options = ExtrudeFaceOptions()
    if merge:
        options.ExtrudeType = ExtrudeType.Add
    else:
        options.ExtrudeType = ExtrudeType.ForceIndependent
    ExtrudeFaces.Execute(select(face), direction, length, 
                         options)

def sweep(face, curve, merge=False):
    options = SweepCommandOptions()
    if merge:
        options.ExtrudeType = ExtrudeType.Add
    else:
        options.ExtrudeType = ExtrudeType.ForceIndependent
    options.Select = True
    Sweep.Execute(face, curve, options)

def move(item, direction, length):
    options = MoveOptions()
    Move.Translate(select(item), direction, length, 
                   options)

def copy(name, item, direction, length):
    Copy.ToClipboard(select(item))
    new = Paste.FromClipboard().CreatedObjects[0]
    move(new, direction, length)
    new.SetName(name)

def split_by_plane(body, cutter):
    SplitBody.ByCutter(select(body), select(cutter))

def split_by_face(body, cutter):
    SplitBody.ByCutter(select(body), select(cutter), True)

def merge_bodies(bodies):
    result = Combine.Merge(select(bodies))

def component(bodies):
    ComponentHelper.MoveBodiesToComponent(select(bodies))

''' -------------------------------------------------------
named selections operations
------------------------------------------------------- '''
def named_selection(name, items, condition=lambda x: True):
    temp = []
    for item in items:
        if condition(item):
            temp.append(item)
    select = Selection.Create(temp)
    NamedSelection.Create(select, Selection.Empty())
    NamedSelection.Rename('Группа1', name)
    return temp

def gather_faces(bodies):
    faces = []
    for body in bodies:
        faces += body.Faces
    return faces

def gather_edges(bodies):
    edges = []
    for body in bodies:
        for face in body.Faces:
            edges += face.Edges
    return edges

''' -------------------------------------------------------
finishing operations
------------------------------------------------------- '''
def delete(*args):
    for item in args:
        if item:
            Delete.Execute(select(item))

def delete_all():
    delete(GetRootPart().Bodies,
           GetRootPart().Components,
           GetRootPart().DatumPlanes,
           GetRootPart().DatumLines,
           GetRootPart().DatumPoints)

def share_topology(tolerance=MM(.1)):
    options = ShareTopologyOptions()
    options.Tolerance = tolerance
    options.PreserveInstances = False
    ShareTopology.FindAndFix(options)

def save(path):
    path = '{}.scdoc'.format(path)
    options = ExportOptions.Create()
    DocumentSave.Execute(path, options)

def zoom():
    Selection.Clear()
    ViewHelper.ZoomToEntity()


''' -------------------------------------------------------
START FROM HERE
------------------------------------------------------- '''
''' -------------------------------------------------------
define parameters
------------------------------------------------------- '''
TOL = MM(.05)
RTOL = 1e-3

radius = MM(5.)
diameter = 2 * radius
length_all = 50 * diameter
length_stb = 10 * diameter
length_tst = length_all - 2 * length_stb

split = .74

''' -------------------------------------------------------
define builder function
------------------------------------------------------- '''

def builder():

    delete_all()
    GetRootPart().SetName('pipe')

    ogrid = radius * split

    ''' -------------------------------------------------------
    create all at once
    ------------------------------------------------------- '''
    ''' middle rectangle '''
    sketch = Sketch(Plane.PlaneXY)
    sketch.polygon((ogrid, 0, 0), 
                   (0, ogrid, 0), 
                   (-ogrid, 0, 0), 
                   (0, -ogrid, 0))
    result = sketch.finish()
    extrude(result, Direction.DirZ, length_all - length_stb)

    ''' outer part '''
    sketch = Sketch(Plane.PlaneXY)
    sketch.polygon((ogrid, 0, 0), 
                   (0, ogrid, 0), 
                   (-ogrid, 0, 0), 
                   (0, -ogrid, 0))
    frame_1 = frame((0, 0, 0), Direction.DirX, Direction.DirY)
    sketch.circle(frame_1, radius)
    result = sketch.finish()
    extrude(result, Direction.DirZ, length_all - length_stb)

    ''' make axial and radial cuts '''
    cut_radial_1 = datum_plane((0, 0, 0),
                               Direction.DirX, Direction.DirZ)
    cut_radial_2 = datum_plane((0, 0, 0),
                               Direction.DirY, Direction.DirZ)
    split_by_plane(GetRootPart().Bodies[1], cut_radial_1)
    split_by_plane(GetRootPart().Bodies[1], cut_radial_2)
    split_by_plane(GetRootPart().Bodies[2], cut_radial_2)

    cut_axial = datum_plane((0, 0, length_stb),
                            Direction.DirX, Direction.DirY)
    for body in GetRootPart().Bodies:
        split_by_plane(body, cut_axial)

    ''' form components - copy '''
    component(GetRootPart().Bodies[5:])
    component(GetRootPart().Bodies[:5])

    copy('stab', GetRootPart().Components[-1], Direction.DirZ,
         length_all - length_stb)

    ''' trash and share topology '''
    zoom()
    delete(GetRootPart().DatumPlanes)
    share_topology(TOL)

    ''' -------------------------------------------------------
    create named selections
    ------------------------------------------------------- '''
    ''' helpful functions '''
    face_up = lambda x: x.GetFaceNormal(0, 0).Z == 1
    face_dn = lambda x: x.GetFaceNormal(0, 0).Z == -1
    equals = lambda x, y: abs(x - y)/y <= RTOL

    ''' define the tree '''
    test  = GetRootPart().Components[0]
    stab1 = GetRootPart().Components[1]
    stab2 = GetRootPart().Components[2]

    test.SetName('test')
    stab1.SetName('stab')
    stab2.SetName('stab')

    ''' fluent named selections '''
    bodies = stab1.GetBodies() + stab2.GetBodies() + \
             test.GetBodies()
    named_selection('fluid', bodies)

    faces_stab_1 = gather_faces(stab1.GetBodies())
    named_selection('inlet', faces_stab_1, face_dn)

    faces_stab_2 = gather_faces(stab2.GetBodies())
    named_selection('outlet', faces_stab_2, face_up)

    faces = faces_stab_1 + faces_stab_2
    area = .5 * math.pi * radius * length_stb
    named_selection('wall-out', faces, 
                         lambda x: equals(x.Area, area))

    faces = gather_faces(bodies)
    area = .5 * math.pi * radius * length_tst
    named_selection('wall', faces, 
                         lambda x: equals(x.Area, area))

    ''' mesher named selections '''
    edges = gather_edges(bodies)
    length_1 = 2 ** .5 * ogrid
    length_2 = .5 * math.pi
    named_selection('tan', edges,
        lambda x: equals(x.GetInterval().Span, length_1) or
                  equals(x.GetInterval().Span, length_2))

    named_selection('rad', edges,
        lambda x: equals(x.GetInterval().Span, radius - ogrid))

    named_selection('axi1', edges,
        lambda x: equals(x.GetInterval().Span, length_tst))

    named_selection('axi2', edges,
        lambda x: equals(x.GetInterval().Span, length_stb))

    ''' save everything '''
    save('C:\\users\\frenc\\yandexdisk\\cfd\\geo\\3F-00-000')

''' -------------------------------------------------------
start modeling
------------------------------------------------------- '''
builder()
