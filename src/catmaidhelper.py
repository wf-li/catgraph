import numpy as np
from src.catmaidclient import CatmaidClient

class CatmaidHelper(CatmaidClient):
    def __init__(self,base_url,api_token=None,**kwargs):
        super().__init__(base_url,api_token,**kwargs)

        if 'project_id' in kwargs:
            self.pid = kwargs['project_id']

    def set_project(self,pid):
        """ Set project ID
        """
        self.pid = pid

    def get_projects(self):
        """ Get projects available to user
        """
        return self.fetch(
            url = "/projects/",
            method = "get"
            ).json()
    
    def get_skeletons(self):
        """ Return list of skeleton IDs

        Parameters
        ----------
        project : CatmaidProject
            Referencing CatmaidProject.py

        Returns
        -------
        list
            List of skeleton IDs
        """
        self.skeletons = self.fetch(
            url = "/" + str(self.pid) + "/skeletons/",
            method = "get",
            data = {"project_id": self.pid}
            ).json()
        return self.skeletons
    
    def load_skeleton_names(self,skeletons):
        """ Make dictionary associating skeleton ID and skeleton name

        Parameters
        ----------
        project : CatmaidProject
            Referencing CatmaidProject.py
        skeletons : list
            List of skeleton IDs

        Returns
        -------
        dict
            Dictionary {skeleton id : skeleton name}
        """
        data = {'neuronnames': '1',
                'metaannotations': '0'}

        for i in range(len(skeletons)):
            data["skeleton_ids['" + str(i) + "']"] = skeletons[i]

        self.skeleton_names = self.fetch(
            url = "/" + str(self.pid) + "/skeleton/annotationlist",
            method = "post",
            data = data
            ).json()['neuronnames']
        return self.skeleton_names
    
    def node_overview(self,skid):
        """ Get node overview for skeleton
        """
        url = "/" + str(self.pid) + "/skeletons/" + str(skid) + "/node-overview"
        return self.fetch(
            url = url,
            method = "get",
            data = {'project_id': self.pid,
                    'skeleton_id': skid}
            ).json()
    
    def get_bounded_nodes(self,
                          skid,
                          start_tags = "nerve_ring_starts",
                          **kwargs):
        """
        skid: int
            skeleton id
        start_tags: str or list
            tag text

        kwargs
        nerve_ring_ends
        """
        skeleton_info = self.node_overview(skid)

        if 'end_tags' in kwargs:
            end_tags = kwargs['end_tags']
            end_nodes = compile_tag_list(end_tags, skeleton_info[2])

        start_nodes = compile_tag_list(start_tags,skeleton_info[2])

        if start_nodes:

            tree_info = np.array(skeleton_info[0])[:,:2]

            nodelist = []

            # append nodes to nodeList from start_nodes to (end_nodes or leafnodes)
            for start_node in start_nodes:
                checklist = [start_node]
                while len(checklist) > 0:
                    for node in checklist:
                        nodelist.append(node)
                        if (node in end_nodes):
                            pass
                        elif get_children(tree_info,node):
                            checklist = checklist + (get_children(tree_info,node))
                        checklist.remove(node)
            return {'skid': skid, 'nodelist': nodelist}
        else:
            return

    def get_edges(self,
                  cid,
                  confidence_gate = 5,
                  **kwargs):
        """ Get edges for a connector

        kwargs
        exclude_connectors: str
            can only be 'pre', may add more in future
        bounded_nodes: dict
            nodes to include where key: skeleton and value: nodes
        """
        exc = 0
        bound = 0

        if "exclude_connectors" in kwargs:
            exc = 1
            connector_exclude = kwargs["exclude_connectors"]
        if "bounded_nodes" in kwargs:
            bound = 1
            bounded_nodes = kwargs["bounded_nodes"]

        if exc^bound:
            raise KeyError("Must include values for both exclude_connectors"
                           " and bounded_nodes")
        
        connector_info = self.fetch(
              url = "/" + str(self.pid) + "/connectors/" + str(cid),
              method = "get",
              data = {"project_id": self.pid,
                      "connector_id": cid}
              ).json()
        
        post_list = []
        pre = ''
                      
        pre_in = False
        for link in connector_info['partners']:
            if link['confidence'] < confidence_gate:
                continue
            if link['relation_name'] == 'presynaptic_to':
                pre = skeleton_names[str(link['skeleton_id'])]
                if connector_exclude == "pre":
                    if pre in skeleton_node_list.keys():
                        pre_in = link['partner_id'] in bounded_nodes[pre]
                    else:
                        continue
            elif link['relation_name'] == 'postsynaptic_to':
                post_list.append(skeleton_names[str(link['skeleton_id'])])
        
        return [[pre,post] for post in post_list]
    
def compile_tag_list(tags,tag_info):
    """ return list of nodes with tag

    Parameters
    ----------
    tag : str
        tag to search for
    tag_info : list
        list of nodes associated with tags [[id1,tag1],[id2,tag2]...]

    Returns
    -------
    List
        List of nodes associated with tag
    """
    if type(tags) == str:
        tags = [tags]
    
    nodes = []
    for tag in tags:
        tag_indices = [(i, skeleton.index(tag))
                         for i, skeleton in enumerate(tag_info)
                         if tag in skeleton]
        if not tag_indices:
            pass
        else:
            for i in tag_indices:
                nodes.append(tag_info[i[0]][0])
    return nodes

def get_children(tree_info,node):
    """ return node IDs of children of reference node

    Parameters
    ----------
    tree_info : numpy array
        2D array of node IDs with 2 columns ['node ID', 'parent ID']
    node : int
        node id

    Returns
    -------
    list
        List of node IDs of children of reference node.
        If reference node has no children, returns 0
    """
    nodelist = []
    node_search = np.where(tree_info[:,1] == node)[0]
    if node_search.size != 0:
        for i in node_search:
            nodelist.append(tree_info[i][0])
        return nodelist
    else:
        return 0


if __name__ == "__main__":

    # test code
    base_url = "https://zhencatmaid.com"

    f = open("C:/Users/liwil/Desktop/work/meizhenlab/apitoken.txt", "r")
    api_token = f.read().replace('\n', '')
    f.close()

    test = CatmaidHelper(base_url = base_url,
                            api_token = api_token)
    
    proj_dict = {}

    projects = test.get_projects()

    for project in projects:
        proj_dict[project['title']] = project["id"]

    print(proj_dict)
    
