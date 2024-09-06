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
from nomad.metainfo import Quantity, SchemaPackage, SubSection, Reference

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

from simulationworkflowschema import SerialSimulation


class WannierPlusEDMFT(SerialSimulation):
    """
    Wannier90 + eDMFT workflow
    """

    # tasks = SubSection(Tasks, repeats=True)

    def normalize(self, archive, logger):
        super().normalize(archive, logger)

        tb_task = self.tasks[0]
        dmft_task = self.tasks[1]



class FreeEnergyPath(SerialSimulation):

    free_energy = Quantity(type=np.float64, unit='joule', shape=['*'])
    positions = Quantity(type=np.float64, unit='meter', shape=['*'])

    def normalize(self, archive, logger):
        super().normalize(archive, logger)

        free_energy = []
        positions = []
        for task in self.tasks:
            free_energy.append(task.outputs.free_energy.value)
            positions.append(task.outputs.x.value)
        self.free_energy = free_energy
        self.positions = positions



m_package.__init_metainfo__()
