import math
import time

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

def component(bodies):
    ComponentHelper.MoveBodiesToComponent(select(bodies))

''' -------------------------------------------------------
named selections operations
------------------------------------------------------- '''
def named_selection(name, items):
    select = Selection.Create(items)
    NamedSelection.Create(select, Selection.Empty())
    NamedSelection.Rename('Группа1', name)

def equals(x, y):
    if y != 0:
        return abs(x - y)/y <= 1e-3
    else:
        return abs(x) <= 1e-3

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
TOL = MM(.01)

radius = MM(5.)
diameter = 2 * radius
length_all = 50 * diameter
length_stb = 10 * diameter

''' -------------------------------------------------------
define builder function
------------------------------------------------------- '''
def builder():
    
    delete_all()

    ''' -------------------------------------------------------
    create sections
    ------------------------------------------------------- '''
    ''' all 3 sketches are on YZ plane '''
    sketch_plane = Plane.PlaneYZ

    ''' stabilizers '''
    sketch = Sketch(sketch_plane)
    sketch.polygon(
        (0, 0, 0),
        (0, radius, 0),
        (0, radius, length_stb),
        (0, 0, length_stb))
    result = sketch.finish()

    ''' move to component - translate - copy '''
    component(GetRootPart().Bodies)
    stab = GetRootPart().Components[-1]

    copy('stab', stab, Direction.DirZ, length_all - length_stb)

    ''' test section '''
    sketch = Sketch(sketch_plane)
    sketch.polygon(
        (0, 0, length_stb),
        (0, radius, length_stb),
        (0, radius, length_all - length_stb),
        (0, 0, length_all - length_stb))
    result = sketch.finish()

    component(GetRootPart().Bodies)
    GetRootPart().Components[-1].SetName('test')

    ''' trash and share topology '''
    zoom()
    share_topology(TOL)
    
    ''' -------------------------------------------------------
    create named selections
    ------------------------------------------------------- '''
    ''' define the tree '''
    test1 = GetRootPart().Components[-1]
    stab1 = GetRootPart().Components[0]
    stab2 = GetRootPart().Components[1]

    ''' fluent named selections '''
    stab1_bodies = stab1.GetBodies()
    stab2_bodies = stab2.GetBodies()
    test1_bodies = test1.GetBodies()
    all_bodies = stab1_bodies + stab2_bodies + test1_bodies

    named_selection('fluid', gather_faces(all_bodies))

    edges = gather_edges(all_bodies)
    select = [x for x in edges if
              equals(x.EvalMid().Point.Y, 0)]
    named_selection('axis', select)

    edges = gather_edges(stab1_bodies)
    select = [x for x in edges if 
              equals(x.EvalMid().Point.Z, 0)]
    named_selection('inlet', select)

    edges = gather_edges(stab2_bodies)
    select = [x for x in edges if 
        equals(x.EvalMid().Point.Z, length_all)]
    named_selection('outlet', select)

    edges = gather_edges(test1_bodies)
    select = [x for x in edges if
              equals(x.EvalMid().Point.Y, radius)]
    named_selection('wall-fluid', select)

    edges = gather_edges(stab1_bodies + stab2_bodies)
    select = [x for x in edges if
              equals(x.EvalMid().Point.Y, radius)]
    named_selection('wall-out', select)

    ''' mesher named selections '''
    edges = gather_edges(all_bodies)
    spans = [x.GetInterval().Span for x in edges]

    select = [x for x, y in zip(edges, spans) if 
              equals(y, radius)]
    named_selection('rad2', select)

    select = [x for x, y in zip(edges, spans) if
              equals(y, length_all - 2 * length_stb)]
    named_selection('axi1', select)

    select = [x for x, y in zip(edges, spans) if
              equals(y, length_stb)]
    named_selection('axi3', select)

    ''' save everything '''
    save('C:\\users\\frenc\\yandexdisk\\cfd\\geo\\2F-00-000')

''' -------------------------------------------------------
start modeling
------------------------------------------------------- '''
builder()
