import os
import yaml

from .landscaper import LandscaperDirCollection

class ChartsCollection(object):

    def __init__(self, **kwargs):
        self.__root_chart_deploy_dir = kwargs['root']
        self.__provisioner = kwargs['chart_provisioner']
        self.__chart_sets = self.chart_sets()


    def chart_sets(self):
        charts_root_dir = self.__root_chart_deploy_dir
        if self.__provisioner == 'landscaper':
            print("AAAX={0}".format(self.__root_chart_deploy_dir))
            landscaper_files = LandscaperDirCollection(charts_root_dir)
            charts_for_provisioner = landscaper_files.chart_sets
        elif self.__provisioner == 'terraform':
            raise NotImplementedError()
        print("charts_for_provisioner={0}".format(charts_for_provisioner))
        return charts_for_provisioner

    def list(self, cluster_selector=None):
        # if cluster_selector:
        #     retval = [d for d in clouds if d['provisioner'] == cloud_type]
        # else:
        return self.__chart_sets


    def charts_for(self, k8s_provisioner, select_namespaces, select_charts):
        print("CHARTS_FOR={0}".format(self.__chart_sets))
        return self.__chart_sets


    def converge(self, namespaces=[], charts=[]):
        print("chart_sets={0}".format(self.__chart_sets))
        # for chart_definiton in self.__chart_sets:
        #     chart = Chart(chart_definition)
            # chart.converge()