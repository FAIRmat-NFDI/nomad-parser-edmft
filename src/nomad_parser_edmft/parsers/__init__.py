from nomad.config.models.plugins import ParserEntryPoint
from pydantic import Field


class EDMFTParserEntryPoint(ParserEntryPoint):
    parser_class_name: str = Field(
        description="""
        The fully qualified name of the Python class that implements the parser.
        This class must have a function `def parse(self, mainfile, archive, logger)`.
    """
    )

    def load(self):
        from nomad.parsing import MatchingParserInterface

        return MatchingParserInterface(**self.dict())


parser_entry_point = EDMFTParserEntryPoint(
    name='parsers/edmft',
    aliases=['parsers/edmft'],
    description='NOMAD parser for EDMFT.',
    mainfile_name_re='.*\.indmfl',
    parser_class_name='nomad_parser_edmft.parsers.parser.EDMFTParser',
    level=2,
)
