from typing import List

from SSD.Core.Rendering.backend.Vedo.VedoActor import VedoActor


def do_remove(actor: VedoActor,
              data_keys: List[str]) -> bool:

    # Arrows must be re-added to update the vectors
    if actor.type == 'Arrows' and ('positions' in data_keys or 'vectors' in data_keys):
        return True

    # Markers must be re-added to update the positions
    elif actor.type == 'Markers' and (len(data_keys) > 0 or 'positions' in actor.object_data['normal_to'].updated_fields):
        return True

    return False
