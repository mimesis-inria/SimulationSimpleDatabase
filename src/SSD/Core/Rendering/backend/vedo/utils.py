from typing import List

from SSD.Core.Rendering.backend.vedo.vedo_objet import VedoObject


def do_remove(v_object: VedoObject,
              data_keys: List[str]) -> bool:

    # Arrows must be re-added to update the vectors
    if v_object.type == 'Arrows' and ('positions' in data_keys or 'vectors' in data_keys):
        return True

    # Markers must be re-added to update the positions
    elif v_object.type == 'Markers' and (len(data_keys) > 0 or 'positions' in v_object.object_data['normal_to'].updated_fields):
        return True

    return False
