from taskmap_pb2 import TaskMap
import os

from IPython.display import Image, display
from PIL import Image as Im
import pydot

def parse_taskgraph(taskmap:TaskMap):
    
    parsed_info = {}
    parsed_info["title"] = taskmap.title
    parsed_info["dataset"] = taskmap.dataset
    parsed_info["thumbnail"] = taskmap.thumbnail_url
    parsed_info["steps"] = taskmap.steps
    parsed_info["conditions"] = taskmap.condition_list
    
    # requirements in the form (id, name+amount)
    parsed_info["requirements_dict"] = {requirements.unique_id :f'{requirements.name}, amount: {requirements.amount}' for requirements in taskmap.requirement_list}

    parsed_info["first_step_id"] = get_first_taskgraph_step(taskmap.connection_list, taskmap.steps)
    parsed_info["requirements_step_links"] = get_links_step_ingredients(taskmap.connection_list, parsed_info["requirements_dict"].keys())
    parsed_info["step_links"] = get_step_links(taskmap.connection_list, taskmap.steps)
    parsed_info["all_links"] = get_all_links(taskmap.connection_list)
    parsed_info["logic_nodes_ids"] = {node.unique_id : node.type for node in taskmap.logic_nodes_list}
    parsed_info["visited_nodes"] = set()
    # steps = [step.response.screen.paragraphs[0] for step in taskmap.steps]
    # steps_urls = [step.response.transcript.image_url for step in taskmap.steps]
    # # steps_urls[-1] = "https://tastykitchen.com/recipes/wp-content/uploads/sites/2/2011/06/Dianes-pasta-410x271.jpg"
    # # print(steps_urls)
    
    # dataset = taskmap.dataset
    # thumbnail_url = taskmap.thumbnail_url
    

    
    return parsed_info

def get_first_taskgraph_step(connections, steps):
    """Connection list contains links to both ingredients and next steps."""
    step_ids = {step.unique_id for step in steps}
    # Filter out step ids 
    nodes_from = {connenction.id_from for connenction in connections}.intersection(step_ids)
    nodes_to = {connenction.id_to for connenction in connections}.intersection(step_ids)
    starting_nodes = nodes_from.difference(nodes_to)
    if len(starting_nodes) != 1:
        raise Exception(f"Cannot determine staring node of the taskgraph. Found {len(starting_nodes)} starting nodes.")
    return starting_nodes.pop()

def get_links_step_ingredients(connections, requirement_ids):
    ingredient_nodes = {connenction.id_from for connenction in connections}.intersection(requirement_ids)
    check_ingredient_link = lambda connection: connection.id_from in ingredient_nodes
    links = list(filter(check_ingredient_link, connections))
    
    links_dict = {} # key: id of a step, val: list[] of ids to ingredients
    for link in links:
        if link.id_to in links_dict:
            links_dict[link.id_to].append(link.id_from)
        else:
            links_dict[link.id_to] = [link.id_from]

    return links_dict

def get_step_links(connections, steps):
    step_ids = {step.unique_id for step in steps}
    
    step_nodes = {connenction.id_from for connenction in connections}.intersection(step_ids)
    check_step_link = lambda connection: connection.id_from in step_nodes
    links = list(filter(check_step_link, connections))
    
    links_dict = {} # key: id of a step, val: list[] of ids to ingredients
    for link in links:
        if link.id_from in links_dict:
            links_dict[link.id_from].append(link.id_to)
        else:
            links_dict[link.id_from] = [link.id_to]
            
    return links_dict

def get_all_links(connections):
    links_dict = {} # key: id of a node, val: list[] of ids to next node
    for link in connections:
        if link.id_from in links_dict:
            links_dict[link.id_from].append(link.id_to)
        else:
            links_dict[link.id_from] = [link.id_to]
            
    return links_dict
    
    

def read_protobuf_list_from_file(path,  proto_message):
    taskmap = proto_message()
    f = open(path, "rb")
    taskmap.ParseFromString(f.read())
    f.close()
    return taskmap

def view_pydot(pdot):
    plt = Image(pdot.create_png())
    display(plt)
    
def scale_img_by_width(filename):
    basewidth = 150
    img = Im.open(filename)
    wpercent = (basewidth / float(img.size[0]))
    hsize = int((float(img.size[1]) * float(wpercent)))
    img = img.resize((basewidth, hsize), Im.ANTIALIAS)
    img.save(filename)
    
def download_image(url, filename):
    import requests
    
    img_data = requests.get(url).content
    # print(requests.get(url).status_code)
    with open(filename, 'wb') as handler:
        handler.write(img_data)
    scale_img_by_width(filename)
    
def delete_image(filename):
    try:
        os.remove(filename)
    except OSError:
        print("Error while deleting file")

def get_task_visualization(parsed_taskgraph, jupyter_notebook = True):
    
    graph = pydot.Dot(parsed_taskgraph["title"], graph_type='digraph', format="jpg", strict=True)
    
    prev_nodes = []
    node = add_heading(graph, parsed_taskgraph)
    prev_nodes.append(node)
    node = add_thumbnail(graph, parsed_taskgraph)
    prev_nodes.append(node)
    
    step_id = parsed_taskgraph["first_step_id"] 
    
    node = add_requirements(graph, parsed_taskgraph, prev_nodes)
    prev_nodes = [node]
    
    add_step(graph, step_id, parsed_taskgraph, prev_nodes)
    
    if jupyter_notebook:
        view_pydot(graph)
        
def add_heading(graph, parsed_taskgraph):
    title = parsed_taskgraph["title"]
    dataset = parsed_taskgraph["dataset"]
    heading = f"{title} by {dataset}"
    
    heading_node = pydot.Node("title", label=heading)
    heading_node.set_fontsize(14)
    heading_node.set_shape("plaintext")
    graph.add_node(heading_node)
    
    return {
        "id" : "title",
        "show_edge" : False
    }
    
def add_thumbnail(graph, parsed_taskgraph):
    img_name = "thumbnail.jpg"
    download_image(parsed_taskgraph["thumbnail"], img_name)
    
    imgNode = pydot.Node("thumbnail", label="",)
    imgNode.set_image(os.path.join(os.getcwd(), img_name))
    imgNode.set_shape("plaintext")
    graph.add_node(imgNode)
    
    return {
        "id" : "thumbnail",
        "show_edge" : False
    }
    
def add_requirements(graph, parsed_taskgraph, prev_nodes):
    
    requirements = parsed_taskgraph["requirements_dict"].values()
    requirements_text = []
    if len(requirements) > 0:
        requirements_text.append("Requirements:")
    for idx, requirement in enumerate(requirements):
        requirements_text.append(f"{idx+1}. {requirement}")
    requirements_text = "\l".join(requirements_text)
    
    requirement_node = pydot.Node("requirements", label=f"{requirements_text}\l")
    requirement_node.set_fontsize(10)
    requirement_node.set_shape("note")
    graph.add_node(requirement_node)
    
    add_prev_edges(graph, "requirements", prev_nodes)
    
    return {
        "id" : "requirements",
        "show_edge" : False
    }
    
    
def add_step(graph, step_id, parsed_taskgraph, prev_nodes):
    
    # print("step id", step_id)
    
    steps = [step for step in parsed_taskgraph["steps"] if step.unique_id == step_id]
    # print("all steps",parsed_taskgraph["steps"])
    # print(len(steps))
    # print("steps", [step.unique_id for step in steps])
    
    if step_id == "05a0e671-1b98-4099-a61f-420c81fa32a5":
        return
    
    if len(steps) == 0:
        if step_id in parsed_taskgraph["logic_nodes_ids"] and parsed_taskgraph["logic_nodes_ids"][step_id] ==  "AnyNode":
            nextStep = parsed_taskgraph["all_links"][step_id][0]
            # print("next_step",nextStep)
            add_step(graph, nextStep, parsed_taskgraph, prev_nodes)
            return 
    
    
    step = steps[0]
    
    text_label = shorten_text(step.response.speech_text)
      
    pydot_node = pydot.Node(step_id, label=text_label)
    pydot_node.set_fontsize(14)
    graph.add_node(pydot_node)
    add_prev_edges(graph, step_id, prev_nodes)
    
    prev_n = []
    prev_n.append({
        "id" : step_id,
        "show_edge" : True
    })
    
    next_nodes_dict = parsed_taskgraph["step_links"]
    
    if step_id in next_nodes_dict:
        next_node = next_nodes_dict[step_id]
        # find condition nodes
        conditions_step_ids = {condition.unique_id for condition in parsed_taskgraph["conditions"]}
        # print(conditions_step_ids)
        # print(step_id)
        # print(next_node)
        # check if condition comes next
        if len(next_node) == 1 and next_node[0] in conditions_step_ids:
            add_condtion(graph, next_node[0], parsed_taskgraph, prev_n) 
        # find future nodes
        else:
            # print("FOUND NODES")
            next_steps = next_nodes_dict[step_id]
            for step_id in next_steps:
                add_step(graph, step_id, parsed_taskgraph, prev_n)  
    
    
def add_condtion(graph, condition_id, parsed_taskgraph, prev_nodes):
    # print("ADD condition")
    condition = [condition for condition in parsed_taskgraph["conditions"] if condition_id == condition.unique_id][0]
    
    pydot_node = pydot.Node(condition_id, label=f"{condition.text}")
    pydot_node.set_fontsize(14)
    pydot_node.set_shape("diamond")
    graph.add_node(pydot_node)
    
    add_prev_edges(graph, condition_id, prev_nodes)
    

    
    next_id_1, next_id_2 = parsed_taskgraph["all_links"][condition_id]

    if next_id_1 in parsed_taskgraph["logic_nodes_ids"] and parsed_taskgraph["logic_nodes_ids"][next_id_1] == "NotNode":
        notNode, yesNode = next_id_1, next_id_2
    else:
        yesNode, notNode = next_id_1, next_id_2
    
    # yesNode
    # print("YES")
    yesNode = parsed_taskgraph["all_links"][yesNode][0]
    notNode = parsed_taskgraph["all_links"][notNode][0]
    
    prev_n = []
    prev_n.append({
        "id" : condition_id,
        "show_edge" : True,
        "label" : "YES"
    })

    add_step(graph, yesNode, parsed_taskgraph, prev_n)
    
    prev_n = []
    prev_n.append({
        "id" : condition_id,
        "show_edge" : True,
        "label" : "No"
    })
    add_step(graph, notNode, parsed_taskgraph, prev_n)
    
    # notNode
    
def shorten_text(step_text):
    breakpoint = 10
    words = step_text.split(" ")
    shortened_text = "\n".join([' '.join(words[i:i+breakpoint]) for i in range(0,len(words),breakpoint)])
    return shortened_text
    
def add_prev_edges(graph, id, prev_nodes):
    
    for node in prev_nodes:
        if node["show_edge"]:
            if "label" in node:
                edge = pydot.Edge(node["id"], id, label = node["label"], fontsize="14")
            else:
                edge = pydot.Edge(node["id"], id)
            # edge = pydot.Edge(node["id"], id)
        else:
            edge = pydot.Edge(node["id"], id, color="white")
        graph.add_edge(edge)