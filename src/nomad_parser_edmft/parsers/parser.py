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
from nomad.parsing.parser import MatchingParser
from nomad.units import ureg

from nomad.datamodel.metainfo.workflow import Workflow

from nomad_simulations.schema_packages.general import Simulation, Program
from nomad.parsing.file_parser import Quantity, TextParser, DataTextParser

configuration = config.get_plugin_entry_point(
    'nomad_parser_edmft.parsers:parser_entry_point'
)

from nomad_simulations.schema_packages.model_method import DFT
from nomad_parser_edmft.schema_packages.schema_package import DMFT


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


class NewParser(MatchingParser):
    def parse(
        self,
        mainfile: str,
        archive: 'EntryArchive',
        logger: 'BoundLogger',
        child_archives: dict[str, 'EntryArchive'] = None,
    ) -> None:
        simulation = Simulation()
        archive.data = simulation

        program = Program(name='eDMFT')
        simulation.program = program

        indmfl_parser = INDMFLParser()
        indmfl_parser.mainfile = mainfile
        indmfl_parser.logger = logger
        print(indmfl_parser.get('n_correlated_atoms'))

        dmft = DMFT(hubbard_u=1.0 * ureg('eV'))
        simulation.model_method.append(dmft)


        input_files = get_files(pattern='*.in0', filepath=mainfile)
        input_file = input_files[0]
        in0_parser = In0Parser()
        in0_parser.mainfile = input_file
        in0_parser.logger = logger
        print(in0_parser.get('xc_functional'))

        jac_ladd_dict = {
            'XC_LDA': 'LDA',
        }
        dft = DFT(jacobs_ladder=jac_ladd_dict.get(in0_parser.get('xc_functional')))
        print(dft.jacobs_ladder)