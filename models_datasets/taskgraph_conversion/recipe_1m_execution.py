
import sys
import re

from .task_graph.task_graph import TaskGraph
from .abstract_execution_step import AbstractExecutionStep


class StepRecipe1MExecution(AbstractExecutionStep):

    def __format_step(self, step):
        if "(recipe follows)" in step:
            step = step.replace("(recipe follows)", "")
        if "recipe follows" in step:
            step = step.replace("recipe follows", "")
        if "(see recipe" in step:
            step = re.sub('\(see recipe.*\)', '', step)

        if len(step) <= 8:
            return None
        if step.startswith('*'):
            return None
        if step.startswith('Photograph courtesy'):
            return None
        if step.startswith('Recipe courtesy'):
            return None
        if step.startswith('Recipe adapted'):
            return None
        if 'http' in step:
            return None
        if 'phone' in step:
            return None

        return step

    def update_task_graph(self, document, task_graph: TaskGraph) -> TaskGraph:
        """  Method for processing steps. """
        # Unpack document
        doc_text, images = document
        steps = []
        for inst in doc_text['instructions']:
            inst_formatted = self.__format_step(inst['text'])
            if inst_formatted:
                steps.append((inst['text'], '', ''))

        return self.process_graph(task_graph=task_graph, steps=steps)
