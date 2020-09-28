
#!/usr/bin/env python

import logging
import os
import glob
import yaml

logger = logging.getLogger(__name__)

from kubernetes import config, client

class AccessControl(object):

    def __init__(self, srcglob, namespace, nameprefix):
        self.srcglob = srcglob
        self.namespace = namespace
        self.nameprefix = nameprefix        

    def generateyaml(self):
        loader = AcltLoader()
        loader.loadglob(self.srcglob)
        logger.debug("Merged Specs: %s" % loader.spec)

        generator = ActlGenerator(self.namespace, self.nameprefix)
        l = generator.generatelist(loader.spec)
        return yaml.dump(l)
    
    def purge(self, objectlinks):
        purger = ActlPurger(self.namespace, self.nameprefix)
        status = purger.status()
        logger.debug("Purgable Objects: %s", status)

        purger.purge(status, objectlinks)
        

class AcltLoader(object):

    def __init__(self):
        from collections import defaultdict
        self.spec = defaultdict(list)

    def loadglob(self, globpattern):
        logger.debug("evaluate glob %s" % globpattern)
        for name in glob.glob(globpattern):
            self.loadfile(name)

    def loadfile(self, filepath):
        logger.debug("loading %s" % filepath)
        with open(filepath, 'r') as fs:
            docs = yaml.load_all(fs.read(), Loader=yaml.BaseLoader)
            for doc in docs:
                if not type(doc) is dict:
                    raise ValueError("Invalid document in file")
                
                self.loaddoc(doc)

    def loaddoc(self, doc):
        # TODO: validate apiversion and schema
        spec=doc["spec"]
        logger.debug("Spec: %s" % spec)
        
        for key, value in spec.items():
            self.spec[key].extend(value)

class ActlGenerator(object):

    def __init__(self, namespace, nameprefix):        
        self.namespace = namespace
        self.nameprefix = nameprefix

    def generatelist(self, spec):

        items = []

        # generate actl namespace
        items.append({
            'apiVersion':'v1',
            'kind':'Namespace',
            'metadata' : {
                'name' : self.namespace
            }
        })       

        for key, specs in spec.items():
            fn = getattr(self, "generate_" + key)
            for spec in specs:
                res = fn(spec)
                if isinstance(res, list):
                    items.extend(res)
                else:
                    items.append(res)


        # add the actl label to all objects
        for item in items:
            metadata = item['metadata']
            if not 'labels' in metadata:
                metadata['labels'] = {}
            labels = metadata['labels']
            labels['accesscontrol.world-direct.at/managed'] = "True"

        return {
            "apiVersion" : "v1",
            "kind" : "List",
            "items" : items
        }



    def generate_serviceaccounts(self, spec):
        logger.debug("generate_serviceaccounts spec=%s" % spec)

        return {
            'apiVersion':'v1',
            'kind':'ServiceAccount',
            'metadata' : {
                'name' : spec,
                'namespace' : self.namespace
            }
        }

    def generate_namespaces(self, spec):
        logger.debug("generate_namespaces spec=%s" % spec)

        objects = []

        # the namespace itself
        objects.append({
            'apiVersion':'v1',
            'kind':'Namespace',
            'metadata' : {
                'name' : spec['name']
            }
        })

        # the rolebindings
        for rolebinding in spec['rolebindings']:
            clusterrole = rolebinding['clusterrole']
            serviceaccounts = rolebinding['serviceaccounts']

            for serviceaccount in serviceaccounts:
                objects.append({
                    'apiVersion':'rbac.authorization.k8s.io/v1',
                    'kind':'RoleBinding',
                    'metadata' : {
                        'name' : self.nameprefix + serviceaccount,
                        'namespace' : spec['name']
                    },
                    'roleRef' : {
                        'apiGroup' : 'rbac.authorization.k8s.io',
                        'kind' : 'ClusterRole',
                        'name' : clusterrole
                    },
                    'subjects' : [
                        {
                            'kind' : 'ServiceAccount',
                            'name' : serviceaccount,
                            'namespace' : self.namespace
                        }
                    ]
                })

        # the resourcequota
        objects.append({
            'apiVersion' : 'v1',
            'kind' : 'ResourceQuota',
            'metadata' : {
                'namespace' : spec['name'],
                'name' : self.nameprefix + 'resourcequota'
            },
            'spec' : spec['resourcequota']
        })

        return objects

    def generate_clusterrolesbindings(self, spec):
        logger.debug("generate_clusterrolesbindings spec=%s" % spec)

        objects = []

        clusterrole = spec['clusterrole']
        serviceaccounts = spec['serviceaccounts']

        for serviceaccount in serviceaccounts:
            objects.append({
                'apiVersion':'rbac.authorization.k8s.io/v1',
                'kind':'ClusterRoleBinding',
                'metadata' : {
                    'name' : self.nameprefix + serviceaccount
                },
                'roleRef' : {
                    'apiGroup' : 'rbac.authorization.k8s.io',
                    'kind' : 'ClusterRole',
                    'name' : clusterrole
                },
                'subjects' : [
                    {
                        'kind' : 'ServiceAccount',
                        'name' : serviceaccount,
                        'namespace' : self.namespace
                    }
                ]
            })

        return objects

class ActlPurger(object):

    def __init__(self, namespace, nameprefix):        
        self.namespace = namespace
        self.nameprefix = nameprefix

    def status(self):
        """Returns the links of all existing purgable objects"""

        from .kubectl import kubectl

        res = []

        # list all clusterrolebindings
        output = kubectl(['kubectl', 'get', 'clusterrolebindings', '-l', 'accesscontrol.world-direct.at/managed=True', '-o', "jsonpath={range .items[*].metadata}{\"- \"}{@.selfLink}{\"\\n\"}"])
        r = yaml.safe_load(output)
        if r:
            res.extend(yaml.safe_load(output))

        # list all rolebindings
        output = kubectl(['kubectl', 'get', 'rolebindings', '-A', '-l', 'accesscontrol.world-direct.at/managed=True', '-o', "jsonpath={range .items[*].metadata}{\"- \"}{@.selfLink}{\"\\n\"}"])
        r = yaml.safe_load(output)
        if r:
            res.extend(yaml.safe_load(output))

        # list all serviceaccounts in our namespaces
        output = kubectl(['kubectl', 'get', 'serviceaccounts', '-A', '-l', 'accesscontrol.world-direct.at/managed=True', '-o', "jsonpath={range .items[*].metadata}{\"- \"}{@.selfLink}{\"\\n\"}"])
        r = yaml.safe_load(output)
        if r:
            res.extend(yaml.safe_load(output))

        return res

    def purge(self, purgableObjects, liveObjects):

        from .kubectl import kubectl
        toPurge = set(purgableObjects) - set(liveObjects)

        if(len(toPurge)):
            logger.info("Obsolete Objects: %s" % toPurge)

            for purgeObj in toPurge:
                kubectl(["kubectl", "delete", "--raw", purgeObj])
        else:
            logger.info("No obsolete Objects!")

