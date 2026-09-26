"""ENU mission coordinates; NED only at the PX4 boundary. Small-area WGS84 tangent map."""
import math


def ned_to_enu(p):
    return [p[1], p[0], -p[2]]


def enu_to_ned(p):
    return [p[1], p[0], -p[2]]


def geodetic(p, origin):
    lat, lon, alt = origin
    phi = math.radians(lat)
    a, e2 = 6378137.0, 6.69437999014e-3
    n = a / math.sqrt(1-e2*math.sin(phi)**2)
    meridian = a*(1-e2)/(1-e2*math.sin(phi)**2)**1.5
    return [lon + math.degrees(p[0]/((n+alt)*math.cos(phi))),
            lat + math.degrees(p[1]/(meridian+alt)), alt+p[2]]


def rotate(q, v):
    w, x, y, z = q  # PX4 quaternion FRD -> NED, wxyz
    norm = math.sqrt(sum(a*a for a in q))
    if not .95 < norm < 1.05:
        raise ValueError('Invalid attitude quaternion')
    w, x, y, z = [a/norm for a in q]
    return [(1-2*y*y-2*z*z)*v[0]+2*(x*y-z*w)*v[1]+2*(x*z+y*w)*v[2],
            2*(x*y+z*w)*v[0]+(1-2*x*x-2*z*z)*v[1]+2*(y*z-x*w)*v[2],
            2*(x*z-y*w)*v[0]+2*(y*z+x*w)*v[1]+(1-2*x*x-2*y*y)*v[2]]


def depth_to_world(u, v, depth, k, pose, q):
    if not math.isfinite(depth) or not .2 < depth < 50:
        return None
    # Nadir camera: optical right=body right; optical down=body aft.
    frd = [-(v-k[5])/k[4]*depth, (u-k[2])/k[0]*depth, depth+.12]
    delta = ned_to_enu(rotate(q, frd))
    return [pose[i]+delta[i] for i in range(3)]


def distance(a, b):
    return math.sqrt(sum((x-y)**2 for x, y in zip(a, b)))
