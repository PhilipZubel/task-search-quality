
import sys
import re

from .task_graph.task_graph import TaskGraph
from .task_graph.nodes.requirement_node import RequirementNode
from .abstract_requirements_step import AbstractRequirementsStep


class StepRecipe1MRequirements(AbstractRequirementsStep):

    def __format_requirement(self, requirement):

        if "(from recipe below)" in requirement:
            requirement = requirement.replace("(from recipe below)", "")
        if "(recipe follows)" in requirement:
            requirement = requirement.replace("(recipe follows)", "")
        if "recipe follows" in requirement:
            requirement = requirement.replace("recipe follows", "")

        if "(available" in requirement:
            requirement = re.sub('\(available.*\)', '', requirement)
        if "(sold at" in requirement:
            requirement = re.sub('\(sold at.*\)', '', requirement)
        if "(see recipe" in requirement:
            requirement = re.sub('\(see recipe.*\)', '', requirement)

        if requirement.startswith('Ingredient info:'):
            return None
        if requirement.startswith('Recipe courtesy'):
            return None
        if requirement.startswith('Recipe adapted'):
            return None
        if requirement.startswith('*'):
            return None
        if 'html' in requirement:
            return None
        if len(requirement) <= 2:
            return None

        return requirement

    def update_task_graph(self, document, task_graph: TaskGraph) -> TaskGraph:
        """ Add Recipe 1M+ requirements to task_graph. """
        # Unpack document
        doc_text, images = document

        ingredients = [ing['text'] for ing in doc_text['ingredients']]
        for ing in ingredients:
            ing_formatted = self.__format_requirement(requirement=ing)
            if ing_formatted:
                node = RequirementNode(
                    name=ing,
                    req_type='HARDWARE',
                    amount='',
                    linked_taskmap_id=''
                )
                task_graph.add_node(node)
        return task_graph
