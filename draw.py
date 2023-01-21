# pip install pydot
# sudo apt-get install graphviz
import sys
sys.path.insert(0, 'compiled_protobufs')
from taskmap_pb2 import TaskMap
import os, glob

from IPython.display import Image, display
import pydot
import requests
from PIL import Image as Im

def view_pydot(pdot):
    plt = Image(pdot.create_png())
    display(plt)
    
def download_image(url, id=0):
    # full_path = os.path.join(os.getcwd(), f'picture{id}.jpg')
    img_data = requests.get(url).content
    # print(requests.get(url).status_code)
    filename = f'img_data{id}.jpg'
    with open(filename, 'wb') as handler:
        handler.write(img_data)
    scale_img_by_width(filename)

def scale_img_by_width(filename):
    basewidth = 200
    img = Im.open(filename)
    wpercent = (basewidth / float(img.size[0]))
    hsize = int((float(img.size[1]) * float(wpercent)))
    img = img.resize((basewidth, hsize), Im.ANTIALIAS)
    img.save(filename)



def parse_taskgraph(taskmap:TaskMap):
    print(taskmap)
    title = taskmap.title
    steps = [step.response.screen.paragraphs[0] for step in taskmap.steps]
    steps_urls = [step.response.transcript.image_url for step in taskmap.steps]
    steps_urls[-1] = "https://tastykitchen.com/recipes/wp-content/uploads/sites/2/2011/06/Dianes-pasta-410x271.jpg"
    print(steps_urls)
    requirements = [requirements.name for requirements in taskmap.requirement_list]
    dataset = taskmap.dataset
    
    breakpoint = 15
    multiline_steps = []
    for step in steps:
        words = step.split(" ")
        multiline_steps.append("\n".join([' '.join(words[i:i+breakpoint]) for i in range(0,len(words),breakpoint)]))
        
    parsed_requirements = []
    if len(requirements) > 0:
        parsed_requirements.append("Requirements:")
    for idx, requirement in enumerate(requirements):
        parsed_requirements.append(f"{idx+1}. {requirement}")
    requirements = "\l".join(parsed_requirements)
    
    steps = []
    return {
        "title" : title,
        "steps" : multiline_steps,
        "steps_urls": steps_urls,
        "requirements" : requirements,
        "dataset" : dataset,
    }


def get_visualization(parsed_taskgraph):
    
    # download images
    for idx, img_url in enumerate(parsed_taskgraph["steps_urls"]):
        if img_url != "":
            download_image(img_url, idx)
    
    graph = pydot.Dot(parsed_taskgraph["title"], graph_type='digraph', format="jpg")
    steps = parsed_taskgraph["steps"]
    
    # create title
    title = parsed_taskgraph["title"]
    dataset = parsed_taskgraph["dataset"]
    title_node = pydot.Node(-1, label=f"{title} by {dataset}")
    title_node.set_fontsize(16)
    title_node.set_shape("plaintext")
    graph.add_node(title_node)
    
    requirements_text = parsed_taskgraph["requirements"]
    requirement_node = pydot.Node(-2, label=f"{requirements_text}\l")
    requirement_node.set_fontsize(10)
    requirement_node.set_shape("note")
    graph.add_node(requirement_node)
    
    nodes = []
    steps = ["START"] + steps
    steps.append("FINISH")

    # Add Nodes for steps
    for idx, step in enumerate(steps):
        node = pydot.Node(idx, label=step)
        node.set_shape("box")
        node.set_fontsize(10)
        nodes.append(node)
        graph.add_node(node)
        print(idx)
        if  idx < len(steps) - 2 and parsed_taskgraph["steps_urls"][idx] != "":
            imgNode = pydot.Node(f"i{idx}", label="",)
            imgNode.set_image(os.path.join(os.getcwd(), f'img_data{idx}.jpg'))
            imgNode.set_shape("plaintext")
            graph.add_node(imgNode)
            edge = pydot.Edge(idx, f'i{idx}', color="white")
            edge.set_len(1)
            graph.add_edge(edge)
            

    nodes[0].set_shape("oval")
    nodes[-1].set_shape("oval")
    
    invisible_edge = pydot.Edge(-1, 0,  color="white")
    graph.add_edge(invisible_edge)

    # Add Edges for steps
    for idx in range(0, len(nodes) - 1):
        edge = pydot.Edge(idx, idx+1)
        edge.set_len(1)
        graph.add_edge(edge)
    
    edge = pydot.Edge(-1, -2, color="white")
    graph.add_edge(edge)
    
    edge = pydot.Edge(-2, 0, color="white")
    graph.add_edge(edge)
    
    graph.write_raw('taskgraph.dot')
    graph.write_png('taskgraph.png')
    # view_pydot(graph)

def delete_downloaded_images():
    # Getting All Files List
    fileList = glob.glob('img_data*.jpg', recursive=False)
        
    # Remove all files one by one
    for file in fileList:
        try:
            os.remove(file)
        except OSError:
            print("Error while deleting file")
    
    
def get_taksgraph_visualization(taskmap:TaskMap):
    parsed_taskgraph = parse_taskgraph(taskmap)
    get_visualization(parsed_taskgraph)
    delete_downloaded_images()


    
    

    
    
