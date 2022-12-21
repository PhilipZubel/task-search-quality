
import sys
sys.path.insert(0, './../compiled_protobufs')

from .abstract_attributes_step import AbstractAttributeStep
from .task_graph.task_graph import TaskGraph
from utils import get_taskmap_id, get_credit_from_url


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
