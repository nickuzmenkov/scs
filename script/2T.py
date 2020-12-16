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
        return PlanarBody.Create(self.plane, self.curves).\
            CreatedBody.Faces[0]

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
define loop parameters
------------------------------------------------------- '''
heights = {
    MM(.1): '10',
    MM(.2): '20',
    MM(.3): '30',
    MM(.4): '40',
    MM(.5): '50',
    MM(.6): '60',
    MM(.7): '70'}

pitches = {
    MM(2.5): '025',
    MM(5.0): '050',
    MM(10.): '100',
    MM(15.): '150'}

''' -------------------------------------------------------
define parameters
------------------------------------------------------- '''
TOL = MM(.01)

radius = MM(5.)
diameter = 2 * radius
length_all = 50 * diameter
length_stb = 10 * diameter

delta1 = MM(.48)
delta2 = MM(.05)

''' -------------------------------------------------------
define builder function
------------------------------------------------------- '''
def builder(height, pitch):
    
    delete_all()

    nsecs = int(round((length_all - 2 * length_stb)/pitch))
    ''' -------------------------------------------------------
    create test sections
    ------------------------------------------------------- '''
    ''' all 6 sketches are on YZ plane '''
    sketch_plane = Plane.PlaneYZ

    ''' first half inner '''
    sketch = Sketch(sketch_plane)
    sketch.polygon(
        (0, 0, 0),
        (0, radius - height, 0),
        (0, radius - height, pitch/2 + delta1/2 - delta2),
        (0, 0, pitch/2 + delta1/2 - delta2))
    result = sketch.finish()

    ''' middle part inner '''
    sketch = Sketch(sketch_plane)
    sketch.polygon(
        (0, 0, pitch/2 + delta1/2 - delta2),
        (0, radius - height, pitch/2 + delta1/2 - delta2),
        (0, radius - height, pitch/2 + delta1/2),
        (0, 0, pitch/2 + delta1/2))
    result = sketch.finish()

    ''' second half inner '''
    sketch = Sketch(sketch_plane)
    sketch.polygon(
        (0, 0, pitch/2 + delta1/2),
        (0, radius - height, pitch/2 + delta1/2),
        (0, radius - height, pitch),
        (0, 0, pitch))
    result = sketch.finish()

    ''' first half outer '''
    sketch = Sketch(sketch_plane)
    sketch.polygon(
        (0, radius - height, 0),
        (0, radius, 0),
        (0, radius, pitch/2 - delta1/2),
        (0, radius - height, pitch/2 + delta1/2 - delta2))
    result = sketch.finish()

    ''' mid part outer '''
    sketch = Sketch(sketch_plane)
    sketch.polygon(
        (0, radius - height, pitch/2 + delta1/2 - delta2),
        (0, radius, pitch/2 - delta1/2),
        (0, radius, pitch/2 + delta1/2),
        (0, radius - height, pitch/2 + delta1/2))
    result = sketch.finish()

    ''' second half outer '''
    sketch = Sketch(sketch_plane)
    sketch.polygon(
        (0, radius - height, pitch/2 + delta1/2),
        (0, radius, pitch/2 + delta1/2),
        (0, radius, pitch),
        (0, radius - height, pitch))
    result = sketch.finish()

    ''' move to component - translate - copy '''
    component(GetRootPart().Bodies)
    test = GetRootPart().Components[-1]

    move(test, Direction.DirZ, length_stb)

    for i in range(1, nsecs):
        copy('test', test, Direction.DirZ, i * pitch)
        time.sleep(.5)
    
    ''' -------------------------------------------------------
    create stabilization sections
    ------------------------------------------------------- '''
    ''' inner part '''
    sketch = Sketch(sketch_plane)
    sketch.polygon(
        (0, 0, 0),
        (0, radius - height, 0),
        (0, radius - height, length_stb),
        (0, 0, length_stb))
    result = sketch.finish()
    line_1 = line((0, 0, 0), Direction.DirZ)

    ''' outer part '''
    sketch = Sketch(sketch_plane)
    sketch.polygon(
        (0, radius - height, 0),
        (0, radius, 0),
        (0, radius, length_stb),
        (0, radius - height, length_stb))
    result = sketch.finish()
    line_1 = line((0, 0, 0), Direction.DirZ)

    ''' move to component - translate - copy '''
    component(GetRootPart().Bodies)
    stab = GetRootPart().Components[-1]

    copy('stab', stab, Direction.DirZ, 
         length_stb + nsecs * pitch)

    ''' trash and share topology '''
    zoom()
    delete(GetRootPart().DatumPlanes)
    share_topology(TOL)
    
    ''' -------------------------------------------------------
    create named selections
    ------------------------------------------------------- '''
    ''' define the tree '''
    assert len(GetRootPart().Components) == nsecs + 2

    stab1 = GetRootPart().Components[-2]
    stab2 = GetRootPart().Components[-1]
    tests = GetRootPart().Components[:nsecs]

    ''' fluent named selections '''
    bodies_solid = []
    bodies_fluid = []
    for i in range(nsecs):
        bodies = tests[i].GetBodies()
        for j in [0, 1, 2, 3, 5]:
            bodies_fluid.append(bodies[j])
        bodies_solid.append(bodies[4])

    edges = gather_edges(bodies_fluid)
    select = [x for x in edges if
              equals(x.EvalMid().Point.Y, radius)]
    named_selection('wall-fluid', select)

    bodies_fluid += stab1.GetBodies() + stab2.GetBodies()
    named_selection('solid', gather_faces(bodies_solid))
    named_selection('fluid', gather_faces(bodies_fluid))

    edges_stab_1 = gather_edges(stab1.GetBodies())
    select = [x for x in edges_stab_1 if 
              equals(x.EvalMid().Point.Z, 0)]
    named_selection('inlet', select)

    edges_stab_2 = gather_edges(stab2.GetBodies())
    select = [x for x in edges_stab_2 if 
        equals(x.EvalMid().Point.Z, 2 * length_stb + nsecs * pitch)]
    named_selection('outlet', select)

    edges = gather_edges(bodies_solid)
    select = [x for x in edges if
              equals(x.EvalMid().Point.Y, radius)]
    named_selection('wall-solid', select)

    select = [x for x in edges if
              not equals(x.EvalMid().Point.Y, radius)]
    named_selection('sides', select)

    bodies = [stab1.GetBodies()[1], stab2.GetBodies()[1]]
    edges = gather_edges(bodies)
    select = [x for x in edges if
              equals(x.EvalMid().Point.Y, radius)]
    named_selection('wall-out', select)

    edges = gather_edges(bodies_solid + bodies_fluid)
    select = [x for x in edges if
              equals(x.EvalMid().Point.Y, 0)]
    named_selection('axis', select)

    ''' mesher named selections '''
    edges = gather_edges(bodies_solid + bodies_fluid)
    spans = [x.GetInterval().Span for x in edges]

    select = [x for x in edges if
              equals(x.EvalMid().Point.Y, radius - height/2)]
    named_selection('rad1', select)

    select = [x for x in edges if
              equals(x.EvalMid().Point.Y, radius/2 - height/2)]
    named_selection('rad2', select)

    select = [x for x, y in zip(edges, spans) if
              equals(y, pitch/2 - delta1/2) or
              equals(y, pitch/2 + delta1/2 - delta2)]
    named_selection('axi1', select)

    select = [x for x, y in zip(edges, spans) if
              equals(y, delta1) or equals(y, delta2)]
    named_selection('axi2', select)

    select = [x for x, y in zip(edges, spans) if
              equals(y, length_stb)]
    named_selection('axi3', select)

    ''' save everything '''
    save('C:\\users\\frenc\\yandexdisk\\cfd\\geo\\2T-{}-{}'.\
         format(heights.get(height), pitches.get(pitch)))

''' -------------------------------------------------------
start modeling
------------------------------------------------------- '''
for pitch in pitches.keys():
    for height in heights.keys():
        builder(height, pitch)
