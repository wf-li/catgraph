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
        return self.fetch(
            url = "/" + str(self.pid) + "/skeletons/",
            method = "get",
            data = {"project_id": self.pid}
            ).json()
    
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

        return self.fetch(
            url = "/" + str(self.pid) + "/skeleton/annotationlist",
            method = "post",
            data = data
            ).json()['neuronnames']
    
    def node_overview(self,skid):
        """ Get node overview for skeleton
        """
        url = str(self.pid) + "/skeletons/" + str(skid) + "/node-overview"
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
            end_tags = kwargs['nerve_ring_starts']
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
    
def compile_tag_list(tag,tag_info):
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
    nodes = []
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
    