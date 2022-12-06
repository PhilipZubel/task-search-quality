
import sys
sys.path.insert(0, './../compiled_protobufs')

from task_graph.task_graph import TaskGraph

from abc import ABC, abstractmethod

import hashlib

class AbstractAttributeStep(ABC):

    @abstractmethod
    def update_task_graph(self, document, task_graph: TaskGraph) -> TaskGraph:
        """ Method for processing steps. """
        pass