import argparse
from collections import defaultdict
from pxr import Usd, UsdGeom
import skia


def get_udim_from_uv(u, v):
    if u < 0 or u > 10 or v < 0:
        return -1
    return 1001 + int(v) * 10 + int(u)

def get_polygon_from_face(face_uvs, uv_positions):
    polygon = []
    for uv_index in face_uvs:
        position = uv_positions[uv_index]
        polygon.append(position)
    return polygon

def get_uv_edges_from_face(face_uvs, uv_positions):
    edges = {}
    for i in range(len(face_uvs)):
        a, b = face_uvs[i], face_uvs[(i + 1) % len(face_uvs)]
        if a > b:
            a, b = b, a
        edges[(a, b)] = (uv_positions[a], uv_positions[b])
    return edges

def get_settings():
    parser = argparse.ArgumentParser(description="Debug argparse")
    
    parser.add_argument("--path", type=str, default="./example.usd", help="Path to the USD file")
    parser.add_argument("--output_path", type=str, default="output.png", help="Output file path")
    parser.add_argument("-s", "--size", type=int, default=2048, help="Image size")

    args = parser.parse_args()

    args.internal_edges = skia.Paint(
        AntiAlias=True,
        Color=skia.Color4f(0, 0, 0, 1),
        Style=skia.Paint.kStroke_Style,
        StrokeWidth=2,
    )

    args.border_edges = skia.Paint(
        AntiAlias=True,
        Color=skia.Color4f(1, 1, 1, 1),
        Style=skia.Paint.kStroke_Style,
        StrokeWidth=4,
    )

    args.front_facing = skia.Paint(
        AntiAlias=True,
        Color=skia.Color4f(0, 0, 1, 0.5),
        Style=skia.Paint.kFill_Style,
    )

    args.back_facing = skia.Paint(
        AntiAlias=True,
        Color=skia.Color4f(1, 0, 0, 0.5),
        Style=skia.Paint.kFill_Style,
    )

    return args

def is_front_facing(faces):
    area = 0
    for i in range(len(faces)):
        u1, v1 = faces[i]
        u2, v2 = faces[(i + 1) % len(faces)]
        area += (u2 - u1) * (v2 + v1)
    return area < 0

def build_graph(edges):
    graph = defaultdict(list)
    for a, b in edges:
        graph[a].append(b)
        graph[b].append(a)
    return graph

def traverse_graph(graph, visited, current):
    path = []
    stack = [current]

    while stack:
        node = stack.pop()
        if node not in visited:
            visited.add(node)
            path.append(node)
            stack.extend(graph[node])
    return path

def get_paths_from_graph(graph):
    visited = set()
    paths = []
    for key in graph:
        if key in visited:
            continue
        else:
            paths.append(traverse_graph(graph, visited, key))
    return paths
    
        
def main():
    settings = get_settings()
    stage = Usd.Stage.Open(settings.path)
    mesh_prims = [x for x in stage.Traverse() if x.IsA(UsdGeom.Mesh)]

    surface = skia.Surface(settings.size, settings.size)
    canvas = surface.getCanvas()
    canvas.clear(skia.Color4f(1, 1, 1, 0))

    for prim in mesh_prims:
        mesh = UsdGeom.Mesh(prim)
        uv_prim_vars = UsdGeom.PrimvarsAPI(mesh).GetPrimvar("st")
        uv_positions = uv_prim_vars.Get(Usd.TimeCode.Default())

        polygons = []
        uv_edges = {}

        if uv_prim_vars:
            face_vert_count = mesh.GetFaceVertexCountsAttr().Get()
            uv_indicies = uv_prim_vars.GetIndices(Usd.TimeCode.Default())

            index = 0
            for idx, count in enumerate(face_vert_count):
                face_uvs = uv_indicies[index:index + count]
                edges = get_uv_edges_from_face(face_uvs, uv_positions)
                polygons.append(get_polygon_from_face(face_uvs, uv_positions))
                for edge, val in edges.items():
                    uv_edges[edge] = uv_edges.get(edge, 0) + 1
                index += count
                
        adjecency_list = [ edge for edge in uv_edges if uv_edges[edge] == 1 ]
        graph = build_graph(adjecency_list)
        paths = get_paths_from_graph(graph)
        
        
        for polygon in polygons:
            scaled_polygon = [
                skia.Point(uv[0] * settings.size, (1 - uv[1]) * settings.size)
                for uv in polygon
            ]
            path = skia.Path()
            path.addPoly(scaled_polygon, close=True)
            canvas.drawPath(path, settings.front_facing if is_front_facing(polygon) else settings.back_facing)
            canvas.drawPath(path, settings.internal_edges)


        for path in paths:
            scaled_path = [
                skia.Point(uv_positions[idx][0] * settings.size, (1 - uv_positions[idx][1]) * settings.size)
                for idx in path
            ]
            path_obj = skia.Path()
            path_obj.addPoly(scaled_path, close=True)
            canvas.drawPath(path_obj, settings.border_edges)

    image = surface.makeImageSnapshot()
    image.save(settings.output_path, skia.kPNG)


if __name__ == "__main__":
    main()
