def generate_skybox_egg(output_file="skybox.egg", face_images=None, scale=1):
    """
    Creates a minimal .egg skybox cube with 6 textures.
    
    face_images: dict mapping face name to image path
        keys: 'px', 'nx', 'py', 'ny', 'pz', 'nz'
    """
    if face_images is None:
        face_images = {
            'px': 'kurt/space_bk.png',
            'nx': 'kurt/space_dn.png',
            'py': 'kurt/space_ft.png',
            'ny': 'kurt/space_lf.png',
            'pz': 'kurt/space_rt.png',
            'nz': 'kurt/space_up.png',
        }

    egg_lines = [
        "<CoordinateSystem> { Z-up }",
        "<Group> skybox {",
    ]

    # define vertices
    s = scale
    verts = {
        'v000': (-s, -s, -s),
        'v001': (-s, -s,  s),
        'v010': (-s,  s, -s),
        'v011': (-s,  s,  s),
        'v100': ( s, -s, -s),
        'v101': ( s, -s,  s),
        'v110': ( s,  s, -s),
        'v111': ( s,  s,  s),
    }

    # write vertices
    for name, v in verts.items():
        egg_lines.append(f"<Vertex> {name} {{ {v[0]} {v[1]} {v[2]} }}")

    # map each face to a pair of triangles
    faces = {
        'px': ('v100','v101','v111','v110'),
        'nx': ('v000','v001','v011','v010'),
        'py': ('v010','v011','v111','v110'),
        'ny': ('v000','v001','v101','v100'),
        'pz': ('v001','v011','v111','v101'),
        'nz': ('v000','v010','v110','v100')
    }

    for face_name, verts_face in faces.items():
        egg_lines.append(f"<Polygon> {{ <Texture> {{ {face_images[face_name]} }}")
        egg_lines.append(f"  <VertexRef> {{ {verts_face[0]} {verts_face[1]} {verts_face[2]} }}")
        egg_lines.append(f"  <VertexRef> {{ {verts_face[0]} {verts_face[2]} {verts_face[3]} }}")
        egg_lines.append("}")

    egg_lines.append("}")  # close group

    with open(output_file, "w") as f:
        f.write("\n".join(egg_lines))

    print(f"Skybox .egg file generated: {output_file}")

generate_skybox_egg()