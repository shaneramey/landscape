import os
import yaml

class ChartsCollection(object):

    # def __init__(self, git_branch, cloud_type, **kwargs):
    #     self.__git_branch = git_branch
    #     self.__chart_set_selector = cloud_type
    #     print("cloud_type={0}".format(cloud_type))
    #     self.__root_chart_deploy_dir = kwargs['root']
    #     self.__chart_sets = self.__chart_sets()

    # def __chart_sets(self):
    #     charts_root_dir = self.__root_chart_deploy_dir
    #     charts_subset = self.__chart_set_selector
    #     charts_git_branch = self.__git_branch
    #     landscaper_files = LandscaperChartsCollection(charts_git_branch, charts_subset, charts_root_dir)
    #     charts_for_provisioner = landscaper_files.chart_sets
    #     print("charts_for_provisioner={0}".format(charts_for_provisioner))
    #     return charts_for_provisioner


    def list(self):
        return self.chart_sets
