"""
Prompts Module
Unified management of all Agent System Prompts and Task Prompt templates
"""

from .input_parser import SYSTEM_PROMPT as INPUT_PARSER_SYSTEM_PROMPT
from .input_parser import get_task_prompt as get_input_parser_task_prompt

from .literature_collector import SYSTEM_PROMPT as LITERATURE_COLLECTOR_SYSTEM_PROMPT
from .literature_collector import get_task_prompt as get_literature_collector_task_prompt

from .variable_designer import SYSTEM_PROMPT as VARIABLE_DESIGNER_SYSTEM_PROMPT
from .variable_designer import get_task_prompt as get_variable_designer_task_prompt

from .theory_designer import SYSTEM_PROMPT as THEORY_DESIGNER_SYSTEM_PROMPT
from .theory_designer import get_task_prompt as get_theory_designer_task_prompt

from .model_designer import SYSTEM_PROMPT as MODEL_DESIGNER_SYSTEM_PROMPT
from .model_designer import get_task_prompt as get_model_designer_task_prompt

from .data_analyst import SYSTEM_PROMPT as DATA_ANALYST_SYSTEM_PROMPT
from .data_analyst import get_task_prompt as get_data_analyst_task_prompt

from .report_writer import SYSTEM_PROMPT as REPORT_WRITER_SYSTEM_PROMPT
from .report_writer import get_task_prompt as get_report_writer_task_prompt

from .reviewer import SYSTEM_PROMPT as REVIEWER_SYSTEM_PROMPT
from .reviewer import get_task_prompt as get_reviewer_task_prompt

__all__ = [
    # InputParserAgent
    'INPUT_PARSER_SYSTEM_PROMPT',
    'get_input_parser_task_prompt',

    # LiteratureCollectorAgent
    'LITERATURE_COLLECTOR_SYSTEM_PROMPT',
    'get_literature_collector_task_prompt',

    # VariableDesignerAgent
    'VARIABLE_DESIGNER_SYSTEM_PROMPT',
    'get_variable_designer_task_prompt',

    # TheoryDesignerAgent
    'THEORY_DESIGNER_SYSTEM_PROMPT',
    'get_theory_designer_task_prompt',

    # ModelDesignerAgent
    'MODEL_DESIGNER_SYSTEM_PROMPT',
    'get_model_designer_task_prompt',

    # DataAnalystAgent
    'DATA_ANALYST_SYSTEM_PROMPT',
    'get_data_analyst_task_prompt',

    # ReportWriterAgent
    'REPORT_WRITER_SYSTEM_PROMPT',
    'get_report_writer_task_prompt',

    # ReviewerAgent
    'REVIEWER_SYSTEM_PROMPT',
    'get_reviewer_task_prompt',
]
