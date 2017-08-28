import os
import yaml
import json # FIXME: remove after debug

from .chartscollection_landscaper import LandscaperChartsCollection

class ChartsCollection(object):

    def __init__(self, cluster, **kwargs):
        self.__cloud = cluster
        print("cluster_collection={0}".format(cluster))
        self.__root_chart_deploy_dir = kwargs['root']
        self.__chart_provisioner = kwargs['chart_provisioner']
        self.__chart_sets = self.__chart_sets()


    def __chart_sets(self):
        charts_root_dir = self.__root_chart_deploy_dir
        if self.__chart_provisioner == 'landscaper':
            landscaper_files = LandscaperChartsCollection(charts_root_dir)
            charts_for_provisioner = landscaper_files.chart_sets
        elif self.__chart_provisioner == 'terraform':
            # future: terraform helm provider
            raise NotImplementedError()
        print("charts_for_provisioner={0}".format(charts_for_provisioner))
        return charts_for_provisioner

    def list(self):
        return self.__chart_sets


    def charts_for(self, k8s_provisioner, select_namespaces, select_charts):
        print("CHARTS_FOR={0}".format(json.dumps(self.__chart_sets)))
        return self.__chart_sets


    def converge(self, namespaces=[], charts=[]):
        print("chart_sets={0}".format(self.__chart_sets))
        # for chart_definiton in self.__chart_sets:
        #     chart = Chart(chart_definition)
            # chart.converge()