import math

# ---------------------------------------------------------
# sketching 2D operations
# ---------------------------------------------------------
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

# ---------------------------------------------------------
# primitives
# ---------------------------------------------------------
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

# ---------------------------------------------------------
# manipulating operations
# ---------------------------------------------------------
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

def move(item, (x, y, z)):
    matrix = Matrix.CreateTranslation(Vector.Create(x, y, z))
    item.Transform(matrix)

def copy(name, item, (x, y, z)):
    Copy.ToClipboard(select(item))
    new = Paste.FromClipboard().CreatedObjects[0]
    move(new, (x, y, z))
    new.SetName(name)

def split_by_plane(body, cutter):
    SplitBody.Execute(select(body), select(cutter))

def split_by_face(body, cutter):
    SplitBody.ByCutter(select(body), select(cutter), True)

def merge_bodies(bodies):
    result = Combine.Merge(select(bodies))

def component(bodies):
    ComponentHelper.MoveBodiesToComponent(select(bodies))

# ---------------------------------------------------------
# named selections operations
# ---------------------------------------------------------
def named_selection(name, items, desc=None):
    if desc:
        items = [x for x, d in zip(items, desc) if d]        
    select = Selection.Create(items)
    NamedSelection.Create(select, Selection.Empty())
    NamedSelection.Rename('Group1', name)

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

# ---------------------------------------------------------
# finishing operations
# ---------------------------------------------------------
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
    ShareTopology.FindAndFix(options)

def save(path):
    path = '{}.scdoc'.format(path)
    options = ExportOptions.Create()
    DocumentSave.Execute(path, options)

def zoom():
    Selection.Clear()
    ViewHelper.ZoomToEntity()


# ---------------------------------------------------------
# START FROM HERE
# ---------------------------------------------------------
# ---------------------------------------------------------
# define parameters
# ---------------------------------------------------------
TOL = MM(.01)

radius = MM(5.)
diameter = 2 * radius
length_all = 22 * diameter
length_stb = 10 * diameter

delta = MM(.48)
split = .74

# ---------------------------------------------------------
# define builder function
# ---------------------------------------------------------
def builder(height, pitch):
    
    delete_all()

    ogrid = (radius - height) * split
    nsecs = int(round((length_all - 2 * length_stb)/pitch))

    # ---------------------------------------------------------
    # create test sections
    # ---------------------------------------------------------
    # middle rectangle
    sketch = Sketch(Plane.PlaneXY)
    sketch.polygon((ogrid, 0, 0), 
                   (0, ogrid, 0), 
                   (-ogrid, 0, 0), 
                   (0, -ogrid, 0))
    result = sketch.finish()
    extrude(result, Direction.DirZ, pitch)

    # inner part
    sketch = Sketch(Plane.PlaneXY)
    sketch.polygon((ogrid, 0, 0), 
                   (0, ogrid, 0), 
                   (-ogrid, 0, 0), 
                   (0, -ogrid, 0))
    frame_1 = frame((0, 0, 0), Direction.DirX, Direction.DirY)
    sketch.circle(frame_1, radius - height)
    result = sketch.finish()
    extrude(result, Direction.DirZ, pitch)

    # outer part 3 parts
    # unlike the others is made by revolving aroung line_1
    line_1 = line((0, 0, 0), Direction.DirZ)

    sketch = Sketch(Plane.PlaneYZ)
    sketch.polygon(
        (0, radius - height, 0), 
        (0, radius, 0), 
        (0, radius, pitch/2 - delta/2), 
        (0, radius - height, pitch/2 - delta/2))
    result = sketch.finish()
    revolve(result, line_1)

    sketch = Sketch(Plane.PlaneYZ)
    sketch.polygon(
        (0, radius - height, pitch/2 - delta/2), 
        (0, radius, pitch/2 - delta/2), 
        (0, radius, pitch/2 + delta/2), 
        (0, radius - height, pitch/2 + delta/2))
    result = sketch.finish()
    revolve(result, line_1)

    sketch = Sketch(Plane.PlaneYZ)
    sketch.polygon(
        (0, radius - height, pitch/2 + delta/2), 
        (0, radius, pitch/2 + delta/2), 
        (0, radius, pitch), 
        (0, radius - height, pitch))
    result = sketch.finish()
    revolve(result, line_1)

    # make axial and radial cuts
    cut_axial_1 = datum_plane((0, 0, pitch/2 - delta/2),
                              Direction.DirX, Direction.DirY)
    cut_axial_2 = datum_plane((0, 0, pitch/2 + delta/2),
                              Direction.DirX, Direction.DirY)
    split_by_plane(GetRootPart().Bodies[0], cut_axial_1)
    split_by_plane(GetRootPart().Bodies[1], cut_axial_1)

    split_by_plane(GetRootPart().Bodies[5], cut_axial_2)
    split_by_plane(GetRootPart().Bodies[6], cut_axial_2)

    cut_radial_1 = datum_plane((0, 0, 0),
                               Direction.DirX, Direction.DirZ)
    cut_radial_2 = datum_plane((0, 0, 0),
                               Direction.DirY, Direction.DirZ)
    split_by_plane(GetRootPart().Bodies[1],  cut_radial_1)
    split_by_plane(GetRootPart().Bodies[2],  cut_radial_1)
    split_by_plane(GetRootPart().Bodies[3],  cut_radial_1)
    split_by_plane(GetRootPart().Bodies[4],  cut_radial_1)
    split_by_plane(GetRootPart().Bodies[6],  cut_radial_1)
    split_by_plane(GetRootPart().Bodies[8],  cut_radial_1)

    split_by_plane(GetRootPart().Bodies[1],  cut_radial_2)
    split_by_plane(GetRootPart().Bodies[2],  cut_radial_2)
    split_by_plane(GetRootPart().Bodies[3],  cut_radial_2)
    split_by_plane(GetRootPart().Bodies[4],  cut_radial_2)
    split_by_plane(GetRootPart().Bodies[6],  cut_radial_2)
    split_by_plane(GetRootPart().Bodies[8],  cut_radial_2)
    split_by_plane(GetRootPart().Bodies[9],  cut_radial_2)
    split_by_plane(GetRootPart().Bodies[10], cut_radial_2)
    split_by_plane(GetRootPart().Bodies[11], cut_radial_2)
    split_by_plane(GetRootPart().Bodies[12], cut_radial_2)
    split_by_plane(GetRootPart().Bodies[13], cut_radial_2)
    split_by_plane(GetRootPart().Bodies[14], cut_radial_2)

    # move to component - translate - copy
    component(GetRootPart().Bodies)
    test = GetRootPart().Components[-1]
    test.SetName('test')

    move(test, (0, 0,length_stb))

    for i in range(1, nsecs):
        copy('test', test, (0, 0, i * pitch))

    
    # ---------------------------------------------------------
    # create stabilization sections
    # ---------------------------------------------------------
    # middle rectangle
    sketch = Sketch(Plane.PlaneXY)
    sketch.polygon((ogrid, 0, 0), 
                   (0, ogrid, 0), 
                   (-ogrid, 0, 0), 
                   (0, -ogrid, 0))
    result = sketch.finish()
    extrude(result, Direction.DirZ, length_stb)

    # inner part
    sketch = Sketch(Plane.PlaneXY)
    sketch.polygon(
        (ogrid, 0, 0), 
        (0, ogrid, 0), 
        (-ogrid, 0, 0), 
        (0, -ogrid, 0))
    frame_1 = frame((0, 0, 0), Direction.DirX, Direction.DirY)
    sketch.circle(frame_1, radius - height)
    result = sketch.finish()
    extrude(result, Direction.DirZ, length_stb)

    # outer part by revolving aroung line_1
    line_1 = line((0, 0, 0), Direction.DirZ)

    sketch = Sketch(Plane.PlaneYZ)
    sketch.polygon(
        (0, radius - height, 0), 
        (0, radius, 0), 
        (0, radius, length_stb), 
        (0, radius - height, length_stb))
    result = sketch.finish()
    revolve(result, line_1)

    # make radial cuts
    split_by_plane(GetRootPart().Bodies[1], cut_radial_1)
    split_by_plane(GetRootPart().Bodies[2], cut_radial_1)

    split_by_plane(GetRootPart().Bodies[1], cut_radial_2)
    split_by_plane(GetRootPart().Bodies[2], cut_radial_2)
    split_by_plane(GetRootPart().Bodies[3], cut_radial_2)
    split_by_plane(GetRootPart().Bodies[4], cut_radial_2)

    # move to component - translate - copy
    component(GetRootPart().Bodies)
    stab = GetRootPart().Components[-1]
    stab.SetName('stab')

    copy('stab', stab, (0, 0, length_stb + nsecs * pitch))

    # trash and share topology
    zoom()
    delete(GetRootPart().DatumPlanes)
    share_topology(TOL)
    
    # ---------------------------------------------------------
    # create named selections
    # ---------------------------------------------------------
    # define the tree
    stab1 = GetRootPart().Components[-2]
    stab2 = GetRootPart().Components[-1]
    tests = GetRootPart().Components[:nsecs]

    # fluent named selections
    bodies_solid = []
    bodies_fluid = []
    for i in range(nsecs):
        bodies = tests[i].GetBodies()
        for j in range(27):
            if j in [3, 11, 17, 23]:
                bodies_solid.append(bodies[j])
            else:
                bodies_fluid.append(bodies[j])
    for body in stab1.GetBodies() + stab2.GetBodies():
        bodies_fluid.append(body)
    named_selection('solid', bodies_solid)
    named_selection('fluid', bodies_fluid)

    faces_stab_1 = gather_faces(stab1.GetBodies())
    desc = [equals(x.MidPoint().Point.Z, 0) for x in faces_stab_1]
    named_selection('inlet', faces_stab_1, desc)

    faces_stab_2 = gather_faces(stab2.GetBodies())
    desc = [equals(x.MidPoint().Point.Z, 2 * length_stb + nsecs * pitch) for x in faces_stab_2]
    named_selection('outlet', faces_stab_2, desc)

    faces = faces_stab_1 + faces_stab_2
    area = .5 * math.pi * radius * length_stb
    desc = [equals(x.Area, area) for x in faces]
    named_selection('wall-out', faces, desc)

    faces = gather_faces(bodies_solid + bodies_fluid)
    area = .5 * math.pi * radius * (pitch/2 - delta/2)
    desc = [equals(x.Area, area) for x in faces]
    named_selection('wall-fluid', faces, desc)

    faces = gather_faces(bodies_solid)
    area = .5 * math.pi * radius * delta
    desc = [equals(x.Area, area) for x in faces]
    named_selection('wall-solid', faces, desc)

    area = .5 * math.pi * (radius - height) * delta
    desc = [x.Evaluate(0, 0).Normal.Z != 0 or equals(x.Area, area) for x in faces]
    named_selection('sides', faces, desc)

    # mesher named selections
    edges = gather_edges(bodies_solid + bodies_fluid)
    spans = [x.GetInterval().Span for x in edges]
    length_1 = 2 ** .5 * ogrid
    length_2 = .5 * math.pi
    desc = [equals(x, length_1) or equals(x, length_2) for x in spans]
    named_selection('tan', edges, desc)

    length = height
    desc = [equals(x, length) for x in spans]
    named_selection('rad1', edges, desc)

    length = radius - height - ogrid
    desc = [equals(x, length) for x in spans]
    named_selection('rad2', edges, desc)

    length = pitch/2 - delta/2
    desc = [equals(x, length) for x in spans]
    named_selection('axi1', edges, desc)

    desc = [equals(x, delta) for x in spans]
    named_selection('axi2', edges, desc)

    desc = [equals(x, length_stb) for x in spans]
    named_selection('axi3', edges, desc)

# ---------------------------------------------------------
# start modeling
# ---------------------------------------------------------
height = MM(Parameters.height)
pitch = MM(Parameters.pitch)
builder(height, pitch)
