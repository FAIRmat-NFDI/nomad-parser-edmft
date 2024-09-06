import os
from glob import glob

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
from nomad.units import ureg

from nomad_simulations.schema_packages.general import Simulation, Program
from nomad.parsing.file_parser import Quantity, TextParser

configuration = config.get_plugin_entry_point(
    'nomad_parser_edmft.parsers:parser_entry_point'
)

from nomad_simulations.schema_packages.model_method import DFT
from nomad_parser_edmft.schema_packages.schema_package import DMFT, WannierPlusEDMFT
from simulationworkflowschema import SinglePoint
from nomad.datamodel.metainfo.workflow import Link, TaskReference


def get_files(pattern: str, filepath: str, stripname: str = '', deep: bool = True):
    """Get files following the `pattern` with respect to the file `stripname` (usually this
    being the mainfile of the given parser) up to / down from the `filepath` (`deep=True` going
    down, `deep=False` up)

    Args:
        pattern (str): targeted pattern to be found
        filepath (str): filepath to start the search
        stripname (str, optional): name with respect to which do the search. Defaults to ''.
        deep (bool, optional): boolean setting the path in the folders to scan (down or up). Defaults to down=True.

    Returns:
        list: List of found files.
    """
    for _ in range(10):
        filenames = glob(f'{os.path.dirname(filepath)}/{pattern}')
        pattern = os.path.join('**' if deep else '..', pattern)
        if filenames:
            break

    if len(filenames) > 1:
        # filter files that match
        suffix = os.path.basename(filepath).strip(stripname)
        matches = [f for f in filenames if suffix in f]
        filenames = matches if matches else filenames

    filenames = [f for f in filenames if os.access(f, os.F_OK)]
    return filenames


class INDMFLParser(TextParser):
    def init_quantities(self):
        self._quantities = [
            Quantity(
                'n_correlated_atoms',
                r'(\d+) *\# number of correlated atoms',
                repeats=False,  # or True
            )
        ]


class In0Parser(TextParser):
    def init_quantities(self):
        self._quantities = [
            Quantity(
                'xc_functional',
                r'TOT *([\w\_]+)',
                repeats=False,
            )
        ]


class EDMFTParser:
    def parse(self, filepath: str, archive: 'EntryArchive', logger: 'BoundLogger'):
        simulation = Simulation()
        archive.data = simulation

        program = Program(name='eDMFT')
        simulation.program = program

        indmfl_parser = INDMFLParser()
        indmfl_parser.mainfile = filepath
        indmfl_parser.logger = logger
        print(indmfl_parser.get('n_correlated_atoms'))

        dmft = DMFT(hubbard_u=1.0 * ureg('eV'))
        simulation.model_method.append(dmft)


        input_files = get_files(pattern='*.in0', filepath=filepath)
        input_file = input_files[0]
        in0_parser = In0Parser()
        in0_parser.mainfile = input_file
        in0_parser.logger = logger
        print(in0_parser.get('xc_functional'))

        jac_ladd_dict = {
            'XC_LDA': 'LDA',
        }
        dft = DFT(jacobs_ladder=jac_ladd_dict.get(in0_parser.get('xc_functional')))

        workflow = SinglePoint()
        archive.workflow2 = workflow


        # We try to resolve the entry_id and mainfile of other entries in the upload
        filepath_stripped = filepath.split('raw/')[-1]
        metadata = []
        try:
            from nomad.app.v1.routers.uploads import get_upload_with_read_access
            from nomad.datamodel import User

            upload_id = archive.metadata.upload_id
            upload = get_upload_with_read_access(
                upload_id=upload_id,
                user=User.get(user_id=archive.metadata.main_author.user_id),
            )
            with upload.entries_metadata() as entries_metadata:
                metadata.extend(
                    [[meta.entry_id, meta.mainfile] for meta in entries_metadata]
                )
        except Exception:
            logger.warning(
                'Could not resolve the entry_id and mainfile of other entries in the upload.'
            )
            return

        for entry_id, mainfile in metadata:
            if mainfile == filepath_stripped:  # we skip the current parsed mainfile
                continue
            # We try to load the archive from its context and connect both the CASTEP
            # and the magres entries
            try:
                entry_archive = archive.m_context.load_archive(
                    entry_id, upload_id, None
                )
                program_name = entry_archive.data.program.name
                if program_name == 'Wannier90':
                    workflow = WannierPlusEDMFT()
                    wannier_task = TaskReference(
                        name='Wannier90 simulation',
                        task=entry_archive.workflow2
                    )
                    workflow.m_add_sub_section(WannierPlusEDMFT.tasks, wannier_task)
                    edmft_task = TaskReference(
                        name='eDMFT simulation',
                        task=archive.workflow2
                    )
                    workflow.m_add_sub_section(WannierPlusEDMFT.tasks, edmft_task)
            except Exception:
                continue