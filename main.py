from collections import defaultdict
from typing import List, Dict, Tuple, Set
import skia
from pxr import Usd, UsdGeom

from settings import get_settings, Settings

def get_udim_from_uv(u: float, v: float) -> int:
    """
    Calculate the UDIM tile number based on UV coordinates.

    Args:
        u (float): U coordinate.
        v (float): V coordinate.

    Returns:
        int: UDIM tile number or "-1" if out of bounds.
    """
    if u < 0 or u > 10 or v < 0:
        return -1
    return 1001 + int(v) * 10 + int(u)

def get_udim_from_uvs(uvs: list[tuple[float, float]]) -> int:
    """
    Determine if all UVs in a polygon share the same UDIM and return the UDIM.

    Args:
        uvs (list[tuple[float, float]]): List of UV coordinates.

    Returns:
        int: UDIM tile number or "-1" if UVs span multiple UDIMs or out of bounds.
    """
    udims = {get_udim_from_uv(u, v) for u, v in uvs}
    return udims.pop() if len(udims) == 1 else -1

def get_uv_edges_from_face(face_uvs: List[int], uv_positions: List[Tuple[float, float]]) -> Dict[Tuple[int, int], Tuple[Tuple[float, float], Tuple[float, float]]]:
    """
    Generate edges for a given face based on UV indices and positions.

    Args:
        face_uvs (List[int]): List of UV indices for the face.
        uv_positions (List[Tuple[float, float]]): UV positions for all vertices.

    Returns:
        Dict[Tuple[int, int], Tuple[Tuple[float, float], Tuple[float, float]]]:
        Dictionary of edges with UV positions.
    """
    edges = {}
    for i in range(len(face_uvs)):
        a, b = face_uvs[i], face_uvs[(i + 1) % len(face_uvs)]
        if a > b:
            a, b = b, a
        edges[(a, b)] = (uv_positions[a], uv_positions[b])
    return edges

def is_front_facing(faces: List[Tuple[float, float]]) -> bool:
    """
    Determine if a face is front-facing based on its winding order.

    Args:
        faces (List[Tuple[float, float]]): List of UV positions defining the face.

    Returns:
        bool: True if the face is front-facing, False otherwise.
    """
    area = 0
    for i in range(len(faces)):
        u1, v1 = faces[i]
        u2, v2 = faces[(i + 1) % len(faces)]
        area += (u2 - u1) * (v2 + v1)
    return area < 0

def build_graph(edges: List[Tuple[int, int]]) -> Dict[int, List[int]]:
    """
    Build an adjacency list representation of a graph from a list of edges.

    Args:
        edges (List[Tuple[int, int]]): List of edges.

    Returns:
        Dict[int, List[int]]: Adjacency list of the graph.
    """
    graph = defaultdict(list)
    for a, b in edges:
        graph[a].append(b)
        graph[b].append(a)
    return graph

def traverse_graph(graph: Dict[int, List[int]], visited: Set[int], current: int) -> List[int]:
    """
    Perform a depth-first traversal of the graph.

    Args:
        graph (Dict[int, List[int]]): Adjacency list of the graph.
        visited (Set[int]): Set of visited nodes.
        current (int): Starting node for the traversal.

    Returns:
        List[int]: List of nodes visited in traversal order.
    """
    path = []
    stack = [current]

    while stack:
        node = stack.pop()
        if node not in visited:
            visited.add(node)
            path.append(node)
            stack.extend(graph[node])
    return path

def get_paths_from_graph(graph: Dict[int, List[int]]) -> List[List[int]]:
    """
    Extract all connected paths from the graph.

    Args:
        graph (Dict[int, List[int]]): Adjacency list of the graph.

    Returns:
        List[List[int]]: List of connected paths.
    """
    visited = set()
    paths = []
    for key in graph:
        if key not in visited:
            paths.append(traverse_graph(graph, visited, key))
    return paths

def draw_polygon(polygon: List[Tuple[float, float]], canvas: skia.Canvas, settings: Settings) -> None:
    """
    Draw a polygon on the canvas.

    Args:
        polygon (List[Tuple[float, float]]): List of UV positions defining the polygon.
        canvas (skia.Canvas): Canvas to draw on.
        settings (Settings): Settings object containing drawing parameters.

    Returns:
        None
    """
    scaled_polygon = [
        skia.Point(uv[0] * settings.size, (1 - uv[1]) * settings.size)
        for uv in polygon
    ]
    path = skia.Path()
    path.addPoly(scaled_polygon, close=True)
    canvas.drawPath(path, settings.front_facing if is_front_facing(polygon) else settings.back_facing)
    canvas.drawPath(path, settings.internal_edges)

def draw_border_edges(path: List[int], uv_positions: List[Tuple[float, float]], canvas: skia.Canvas, settings: Settings) -> None:
    """
    Draw the border edges of a path on the canvas.

    Args:
        path (List[int]): List of indices defining the path.
        uv_positions (List[Tuple[float, float]]): UV positions for all vertices.
        canvas (skia.Canvas): Canvas to draw on.
        settings (Settings): Settings object containing drawing parameters.

    Returns:
        None
    """
    scaled_path = [
        skia.Point(uv_positions[idx][0] * settings.size, (1 - uv_positions[idx][1]) * settings.size)
        for idx in path
    ]
    path_obj = skia.Path()
    path_obj.addPoly(scaled_path, close=True)
    canvas.drawPath(path_obj, settings.border_edges)

def get_all_udims_from_a_face(polygon: List[Tuple[float, float]]) -> List[int]:
    """
    Retrieves all unique UDIMs from a face based on its UV coordinates.

    Args:
        polygon (List[Tuple[float, float]]): A list of UV coordinates representing a face.

    Returns:
        List[int]: A list of unique UDIM indices.
    """
    udims = set()
    for u, v in polygon:
        udims.add(get_udim_from_uv(u, v))
    return list(udims)

def get_border_edges(uv_edges: Dict[Tuple[float, float], int]) -> List[List[Tuple[float, float]]]:
    """
    Retrieves the border edges from a set of UV edges.

    Args:
        uv_edges (Dict[Tuple[float, float], int]): A dictionary where keys are UV coordinate
            tuples representing edges and values are the amount of faces associated with that edge.

    Returns:
        List[List[Tuple[float, float]]]: A list of paths, where each path is a list of UV coordinate tuples.
    """
    adjacency_list = [edge for edge in uv_edges if uv_edges[edge] == 1]
    graph = build_graph(adjacency_list)
    return get_paths_from_graph(graph)

def main() -> None:
    """
    Main function to process a USD stage, extract UV data, and draw the mesh.

    Returns:
        None
    """
    settings = get_settings()
    stage = Usd.Stage.Open(settings.path)
    mesh_prims = [x for x in stage.Traverse() if x.IsA(UsdGeom.Mesh)]
    
    skia_surfaces = {}

    for prim in mesh_prims:
            
        mesh = UsdGeom.Mesh(prim)
        uv_prim_vars = UsdGeom.PrimvarsAPI(mesh).GetPrimvar("st")
        uv_positions = uv_prim_vars.Get(Usd.TimeCode.Default())

        polygons = []
        uv_edges = defaultdict(int)

        if uv_prim_vars:
            face_vert_count = mesh.GetFaceVertexCountsAttr().Get()
            uv_indicies = uv_prim_vars.GetIndices(Usd.TimeCode.Default())

            index = 0
            for count in face_vert_count:
                face_uvs = uv_indicies[index:index + count]
                edges = get_uv_edges_from_face(face_uvs, uv_positions)
                polygon = [uv_positions[uv_index] for uv_index in face_uvs]
                polygons.append(polygon)
                for edge in edges:
                    uv_edges[edge] = uv_edges.get(edge, 0) + 1
                index += count

            border_edges = get_border_edges(uv_edges)

            for polygon in polygons:
                udim = get_udim_from_uvs(polygon)
                if udim not in skia_surfaces:
                    skia_surfaces[udim] = skia.Surface(settings.size, settings.size)
                    skia_surfaces[udim].getCanvas().clear(skia.Color4f(1, 1, 1, 0))
              
                if udim != -1:
                    draw_polygon(polygon, skia_surfaces[udim].getCanvas(), settings)

            for border in border_edges:
                udim = get_udim_from_uvs([uv_positions[uv_index] for uv_index in border])
                
                if udim != -1:
                    draw_border_edges(border, uv_positions,  skia_surfaces[udim].getCanvas(), settings)

    
    for surface in skia_surfaces:
        image = skia_surfaces[surface].makeImageSnapshot()
        start, end = settings.output_path.split('#')
        image.save(f"{start}{surface}{end}", skia.kPNG)

if __name__ == "__main__":
    main()
