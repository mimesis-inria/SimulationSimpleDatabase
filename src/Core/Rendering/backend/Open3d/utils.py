from numpy import ndarray, array, matmul, dot, eye
from numpy.linalg import norm


def get_rotation_matrix(vec: ndarray) -> ndarray:
    # Source: https://stackoverflow.com/questions/59026581/create-arrows-in-open3d

    vec_norm = norm(vec)
    vec = vec / vec_norm
    z_unit = array([0., 0., 1.])

    if dot(z_unit, vec) == -1:
        R = -eye(3, 3)
    elif dot(z_unit, vec) == 1:
        R = eye(3, 3)
    else:
        z_mat = get_cross_product(z_unit)
        z_c_vec = matmul(z_mat, vec)
        z_c_mat = get_cross_product(z_c_vec)
        R = eye(3, 3) + z_c_mat + matmul(z_c_mat, z_c_mat) / (1 + dot(z_unit, vec))

    return R


def get_cross_product(vec: ndarray):

    return array([[0.,      -vec[2], vec[1]],
                  [vec[2],  0,       -vec[0]],
                  [-vec[1], vec[0],  0]])

