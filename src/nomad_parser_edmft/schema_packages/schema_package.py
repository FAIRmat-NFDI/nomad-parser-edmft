import numpy as np

from typing import (
    TYPE_CHECKING,
)

if TYPE_CHECKING:
    from nomad.datamodel.datamodel import (
        EntryArchive,
    )
    from structlog.stdlib import (
        BoundLogger,
    )

from nomad.config import config
from nomad.datamodel.data import Schema
from nomad.datamodel.metainfo.annotations import ELNAnnotation, ELNComponentEnum
from nomad.metainfo import Quantity, SchemaPackage

from nomad_simulations.schema_packages.model_method import ModelMethod

configuration = config.get_plugin_entry_point(
    'nomad_parser_edmft.schema_packages:schema_package_entry_point'
)

m_package = SchemaPackage()



class DMFT(ModelMethod):
    
    hubbard_u = Quantity(
        type=np.float64,
        unit='joule',
        description='Hubbard U',
    )


class RPASpectra(ModelMethod):

    damping = Quantity(
        type=np.float64,
        shape=['*', '*'],
        unit='joule',
        description='Damping',
    )



m_package.__init_metainfo__()
