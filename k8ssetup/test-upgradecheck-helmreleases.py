import kubernetes

kubernetes.config.load_kube_config()
api = kubernetes.client.CustomObjectsApi()

namespace = "kube-harbor2"

group = "helm.fluxcd.io"
version = "v1"
plural = "helmreleases"

print("Retrieving %s/%s %s from namespace %s" % (group, version, plural, namespace))

releases = api.list_namespaced_custom_object(group, version, namespace, plural)#, pretty=pretty, _continue=_continue, field_selector=field_selector, label_selector=label_selector, limit=limit, resource_version=resource_version, timeout_seconds=timeout_seconds, watch=watch)
#print(releases)


for release in releases['items']:
    #print("++++++++++++++++++")    
    #print(release)

    objname = release['metadata']['name']
    spec = release['spec']
    chart = spec['chart']
    chart_name = chart['name']
    repository = chart['repository']
    version = chart['version']

    #print("++++++++++++++++++")    
    print("Release '%s' => Repository: '%s' Chart: '%s' Version: '%s'" % (objname, repository, chart_name, version))

    # download the index.yaml from the repp
    import urllib.request
    import yaml

    repo_index = yaml.safe_load(urllib.request.urlopen(repository + "/index.yaml"))
    chart_index = repo_index['entries']['harbor']
    chart_versions = list(map(lambda i: i['version'], chart_index))
    chart_versions.sort(reverse=True)

    #print("++++++++++++++++++")    
    #print(chart_versions)

    latest_version = chart_versions[0]
    print("Latest Version: %s" % latest_version)

    if version < latest_version:
        print("CHART CAN BE UPDATED TO %s" % latest_version)    
    

