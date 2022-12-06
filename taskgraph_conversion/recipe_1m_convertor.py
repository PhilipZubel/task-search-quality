
import sys
sys.path.insert(0, './../compiled_protobufs')

from task_graph import *
from task_graph.task_graph import TaskGraph
# from utils import get_taskmap_id, get_credit_from_url
from abstract_convertor import AbstractConvertor

from recipe_1m_requirements import StepRecipe1MRequirements
from recipe_1m_execution import StepRecipe1MExecution
from abstract_attributes_step import AbstractAttributeStep


def get_taskmap_id(doc_type, dataset, url) -> str:
    """ Generate taskmap_id using MD5 hash. """
    import hashlib
    md5 = hashlib.md5(url.encode('utf-8')).hexdigest()
    return doc_type + '+' + dataset + '+' + md5

def get_credit_from_url(url):
    """ Given a URL return a website name or [UNKNOWN] token."""
    from urllib.parse import urlparse

    domain = urlparse(url).netloc
    if domain:
        website_keyword = domain.split('.')
        if len(website_keyword) > 2:
            website_name = website_keyword[1:-1][0]
        else:
            website_name = domain
        return website_name
    return ''


class Recipe1MConvertor(AbstractConvertor):

    def filter(self, task_graph):
        """ return True is valid else False if not"""
        try:
            taskmap = task_graph.to_proto()
        except:
            return False

        if not taskmap.title:
            return False

        if not taskmap.steps:
            return False

        if len(taskmap.thumbnail_url) == 0:
            return False

        num_requirements = 0 if not taskmap.requirement_list else len(taskmap.requirement_list)
        if num_requirements > 20:
            return False

        num_steps = 0 if not taskmap.steps else len(taskmap.steps)
        if num_steps > 20:
            return False

        max_step_words = max([len(step.response.speech_text.split()) for step in taskmap.steps])
        if max_step_words > 100:
            return False

        min_step_words = min([len(step.response.speech_text.split()) for step in taskmap.steps])
        if min_step_words == 0:
            return False

        return True

    def document_to_task_graph(self, document) -> TaskGraph:
        """ Convert document to TaskGraph. """
        task_graph = TaskGraph()
        task_graph = StepRecipe1MAttributes().update_task_graph(document=document, task_graph=task_graph)
        task_graph = StepRecipe1MRequirements().update_task_graph(document=document, task_graph=task_graph)
        task_graph = StepRecipe1MExecution().update_task_graph(document=document, task_graph=task_graph)
        return task_graph






class StepRecipe1MAttributes(AbstractAttributeStep):

    DOC_TYPE = 'cooking'
    DATASET = 'recipe1m'

    def update_task_graph(self, document, task_graph: TaskGraph) -> TaskGraph:
        """ Add Recipe 1M+ attributes to task_graph. """
        # Unpack document
        doc_text, images = document

        # Dataset
        task_graph.set_attribute('dataset', self.DATASET)

        # Taskmap ID
        url = doc_text['url']
        taskmap_id = get_taskmap_id(doc_type=self.DOC_TYPE, dataset=self.DATASET, url=url)
        task_graph.set_attribute('taskmap_id', taskmap_id)

        # Title
        title = doc_text['title']
        task_graph.set_attribute('title', title)

        # Source URL
        task_graph.set_attribute('source_url', url)

        # Thumbnail URL
        if len(images) > 0:
            if 'foodnetwork' not in url:
                task_graph.set_attribute('thumbnail_url', images[0])

        # Domain name.
        domain_name = get_credit_from_url(url)
        if domain_name:
            task_graph.set_attribute('domain_name', domain_name)

        return task_graph
